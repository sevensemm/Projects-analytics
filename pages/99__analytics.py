import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import Database

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

if not st.session_state.get('is_admin'):
    st.error("Недостаточно прав для доступа к аналитике")
    st.stop()

db = Database()

st.title("📊 Аналитика производительности")

# Инициализация session_state для фильтров
if 'analytics_filters' not in st.session_state:
    st.session_state.analytics_filters = {
        'selected_project': None,
        'selected_project_id': None,
        'selected_stage': None,
        'selected_stage_id': None,
        'start_date': date.today() - timedelta(days=30),
        'end_date': date.today(),
        'show_salaries': True,
        'show_deviations': True
    }

# Боковая панель с фильтрами
with st.sidebar:
    st.header("Фильтры анализа")
    
    # Быстрый выбор проекта
    st.subheader("Быстрый выбор проекта")
    projects_df = db.get_all_projects()
    
    if not projects_df.empty:
        project_dict = {}
        for _, project in projects_df.iterrows():
            project_dict[project['project_name']] = project['project_id']
        
        # Кнопки для быстрого выбора проекта
        cols = st.columns(2)
        project_names = list(project_dict.keys())
        
        for idx, project_name in enumerate(project_names):
            with cols[idx % 2]:
                if st.button(f"📁 {project_name}", key=f"project_btn_{idx}", use_container_width=True):
                    st.session_state.analytics_filters['selected_project'] = project_name
                    st.session_state.analytics_filters['selected_project_id'] = project_dict[project_name]
                    st.session_state.analytics_filters['selected_stage'] = None
                    st.session_state.analytics_filters['selected_stage_id'] = None
                    st.rerun()
    
    st.markdown("---")
    
    # Если проект выбран, показываем детальные фильтры
    if st.session_state.analytics_filters['selected_project']:
        st.write(f"**Выбран проект:** {st.session_state.analytics_filters['selected_project']}")
        
        # Выбор этапа
        project_id = st.session_state.analytics_filters['selected_project_id']
        stages_df = db.get_project_stages(project_id)
        
        if not stages_df.empty:
            st.subheader("Выбор этапа")
            
            # Кнопки для быстрого выбора этапа
            cols = st.columns(2)
            for idx, (_, stage) in enumerate(stages_df.iterrows()):
                with cols[idx % 2]:
                    if st.button(f"📋 {stage['stage_name']}", key=f"stage_btn_{stage['stage_id']}", use_container_width=True):
                        st.session_state.analytics_filters['selected_stage'] = stage['stage_name']
                        st.session_state.analytics_filters['selected_stage_id'] = stage['stage_id']
                        st.rerun()
            
            # Выпадающий список для точного выбора
            stage_options = ["-- Все этапы --"] + stages_df['stage_name'].tolist()
            stage_selected_idx = 0
            
            if st.session_state.analytics_filters['selected_stage'] in stage_options:
                stage_selected_idx = stage_options.index(st.session_state.analytics_filters['selected_stage'])
            
            selected_stage = st.selectbox(
                "Или выберите этап:",
                stage_options,
                index=stage_selected_idx,
                key="stage_select_dropdown"
            )
            
            if selected_stage != "-- Все этапы --" and selected_stage != st.session_state.analytics_filters['selected_stage']:
                stage_info = stages_df[stages_df['stage_name'] == selected_stage].iloc[0]
                st.session_state.analytics_filters['selected_stage'] = selected_stage
                st.session_state.analytics_filters['selected_stage_id'] = stage_info['stage_id']
                st.rerun()
            elif selected_stage == "-- Все этапы --" and st.session_state.analytics_filters['selected_stage']:
                st.session_state.analytics_filters['selected_stage'] = None
                st.session_state.analytics_filters['selected_stage_id'] = None
                st.rerun()
    
    # Период анализа
    st.markdown("---")
    st.subheader("Период анализа")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "С:",
            value=st.session_state.analytics_filters['start_date'],
            key="start_date"
        )
        st.session_state.analytics_filters['start_date'] = start_date
    
    with col2:
        end_date = st.date_input(
            "По:",
            value=st.session_state.analytics_filters['end_date'],
            key="end_date"
        )
        st.session_state.analytics_filters['end_date'] = end_date
    
    # Кнопка сброса фильтров
    if st.button("🔄 Сбросить фильтры", use_container_width=True):
        st.session_state.analytics_filters = {
            'selected_project': None,
            'selected_project_id': None,
            'selected_stage': None,
            'selected_stage_id': None,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today(),
            'show_salaries': True,
            'show_deviations': True
        }
        st.rerun()

# Основная область
if not st.session_state.analytics_filters['selected_project']:
    st.info("ℹ️ Выберите проект для анализа")
    
    # Показываем статистику по всем проектам
    if not projects_df.empty:
        st.subheader("Общая статистика по проектам")
        
        # Собираем статистику по всем проектам
        all_stats = []
        for _, project in projects_df.iterrows():
            project_id = project['project_id']
            project_analytics = db.get_project_analytics(project_id)
            
            if not project_analytics.empty:
                total_revenue = project_analytics['stage_cost'].sum()
                total_tasks = project_analytics['task_count'].sum()
                completed_tasks = project_analytics['completed_count'].sum()
                
                all_stats.append({
                    'Проект': project['project_name'],
                    'Выручка (₽)': total_revenue,
                    'Всего задач': total_tasks,
                    'Выполнено': completed_tasks,
                    'Процент выполнения': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                })
        
        if all_stats:
            stats_df = pd.DataFrame(all_stats)
            
            # 1. Круговая диаграмма выручки по проектам
            if stats_df['Выручка (₽)'].sum() > 0:
                fig1 = px.pie(
                    stats_df,
                    values='Выручка (₽)',
                    names='Проект',
                    title='Распределение выручки по проектам',
                    hover_data=['Всего задач', 'Выполнено'],
                    color_discrete_sequence=px.colors.sequential.Viridis  # Исправлено: убрали color_continuous_scale
                )
                fig1.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig1, use_container_width=True)
            
            # 2. Столбчатая диаграмма эффективности
            fig2 = px.bar(
                stats_df,
                x='Проект',
                y='Процент выполнения',
                title='Процент выполнения задач по проектам',
                color='Процент выполнения',
                color_continuous_scale='RdYlGn',
                text='Процент выполнения'
            )
            fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig2.update_layout(yaxis_title='Выполнение (%)', yaxis_range=[0, 100])
            st.plotly_chart(fig2, use_container_width=True)
            
            # Таблица с данными
            st.dataframe(stats_df, use_container_width=True)
else:
    # Основные вкладки
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Аналитика этапа", 
        "📊 Аналитика проекта", 
        "⏱️ Отклонения от плана", 
        "👥 Эффективность сотрудников"
    ])
    
    project_id = st.session_state.analytics_filters['selected_project_id']
    stages_df = db.get_project_stages(project_id)
    
    # ВКЛАДКА 1: Аналитика этапа
    with tab1:
        if not st.session_state.analytics_filters['selected_stage']:
            st.info("ℹ️ Выберите этап для детального анализа")
            
            if not stages_df.empty:
                # Показываем сводную информацию по всем этапам
                st.subheader("Обзор всех этапов проекта")
                
                # Собираем данные по всем этапам
                stage_stats = []
                for _, stage in stages_df.iterrows():
                    stage_data = db.get_stage_analytics(stage['stage_id'])
                    valid_tasks = stage_data[stage_data['task_id'].notna()]
                    
                    if len(valid_tasks) > 0:
                        total_planned = valid_tasks['planned_hours'].sum()
                        total_actual = valid_tasks['actual_hours'].sum()
                        efficiency = (total_planned / total_actual * 100) if total_actual > 0 else 0
                        completed = len(valid_tasks[valid_tasks['status'] == 'completed'])
                        
                        stage_stats.append({
                            'Этап': stage['stage_name'],
                            'Задачи': len(valid_tasks),
                            'Выполнено': completed,
                            'Эффективность %': round(efficiency, 1),
                            'Стоимость (₽)': stage.get('stage_cost', 0)
                        })
                
                if stage_stats:
                    stats_df = pd.DataFrame(stage_stats)
                    
                    # 1. Круговая диаграмма стоимости этапов
                    if stats_df['Стоимость (₽)'].sum() > 0:
                        # Используем дивергентную цветовую схему RdYlGn для pie chart
                        colors = ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']
                        fig1 = px.pie(
                            stats_df,
                            values='Стоимость (₽)',
                            names='Этап',
                            title='Распределение стоимости по этапам',
                            hover_data=['Задачи', 'Выполнено'],
                            color_discrete_sequence=colors  # Исправлено: явно задаем цвета
                        )
                        fig1.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig1, use_container_width=True)
                    
                    # 2. Пузырьковая диаграмма эффективности
                    fig2 = px.scatter(
                        stats_df,
                        x='Задачи',
                        y='Эффективность %',
                        size='Стоимость (₽)',
                        color='Этап',
                        hover_name='Этап',
                        title='Эффективность этапов (размер пузырька = стоимость)',
                        size_max=60
                    )
                    fig2.update_layout(
                        yaxis_title='Эффективность (%)',
                        xaxis_title='Количество задач',
                        showlegend=True
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    st.dataframe(stats_df, use_container_width=True)
        else:
            # Аналитика конкретного этапа
            stage_id = st.session_state.analytics_filters['selected_stage_id']
            stage_data = db.get_stage_analytics(stage_id)
            stage_info = stages_df[stages_df['stage_id'] == stage_id].iloc[0]
            
            # Фильтруем только задачи
            valid_tasks = stage_data[stage_data['task_id'].notna()]
            
            if len(valid_tasks) > 0:
                # Рассчитываем стоимость задач
                stage_cost = stage_info.get('stage_cost', 0)
                valid_tasks['task_cost'] = 0
                
                if stage_cost > 0:
                    total_hours = valid_tasks['actual_hours'].sum()
                    if total_hours > 0:
                        valid_tasks['task_cost'] = (valid_tasks['actual_hours'] / total_hours) * stage_cost
                
                # 1. Круговая диаграмма распределения времени
                st.subheader("Распределение времени по задачам")
                
                fig1 = px.pie(
                    valid_tasks,
                    values='actual_hours',
                    names='task_name',
                    title=f'Распределение времени по задачам ({st.session_state.analytics_filters["selected_stage"]})',
                    color='status',
                    color_discrete_map={'completed': '#2ecc71', 'pending': '#f39c12'},
                    hover_data=['responsible_name', 'planned_hours']
                )
                fig1.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig1, use_container_width=True)
                
                # 2. Круговая диаграмма распределения стоимости
                
                
                # 3. Гистограмма плана vs факта
                st.subheader("Сравнение плановых и фактических часов")
                
                fig3 = go.Figure()
                
                fig3.add_trace(go.Bar(
                    x=valid_tasks['task_name'],
                    y=valid_tasks['planned_hours'],
                    name='Плановые часы',
                    marker_color='#3498db',
                    text=valid_tasks['planned_hours'].round(1),
                    textposition='auto'
                ))
                
                fig3.add_trace(go.Bar(
                    x=valid_tasks['task_name'],
                    y=valid_tasks['actual_hours'],
                    name='Фактические часы',
                    marker_color='#e74c3c',
                    text=valid_tasks['actual_hours'].round(1),
                    textposition='auto'
                ))
                
                fig3.update_layout(
                    title='План vs Факт по задачам',
                    xaxis_title='Задачи',
                    yaxis_title='Часы',
                    barmode='group',
                    hovermode='x unified',
                    showlegend=True
                )
                
                st.plotly_chart(fig3, use_container_width=True)
                
                # Статистика
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Стоимость этапа", f"{stage_cost:,.0f} ₽")
                with col2:
                    st.metric("Задач в этапе", len(valid_tasks))
                with col3:
                    completed = len(valid_tasks[valid_tasks['status'] == 'completed'])
                    st.metric("Выполнено", f"{completed}/{len(valid_tasks)}")
                with col4:
                    total_planned = valid_tasks['planned_hours'].sum()
                    total_actual = valid_tasks['actual_hours'].sum()
                    efficiency = (total_planned / total_actual * 100) if total_actual > 0 else 0
                    st.metric("Эффективность", f"{efficiency:.1f}%")
                
                # Таблица
                display_df = valid_tasks[['task_name', 'responsible_name', 'status', 
                                        'planned_hours', 'actual_hours', 'task_cost']].copy()
                display_df.columns = ['Задача', 'Ответственный', 'Статус', 
                                    'План. часы', 'Факт. часы', 'Стоимость (₽)']
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("📝 В этапе нет задач")
    
    # ВКЛАДКА 2: Аналитика проекта
    with tab2:
        project_analytics = db.get_project_analytics(project_id)
        
        if not project_analytics.empty:
            # 1. Круговая диаграмма выручки по этапам
            st.subheader("Распределение выручки по этапам")
            
            total_revenue = project_analytics['stage_cost'].sum()
            if total_revenue > 0:
                fig1 = px.pie(
                    project_analytics,
                    values='stage_cost',
                    names='stage_name',
                    title=f'Выручка по этапам ({st.session_state.analytics_filters["selected_project"]})',
                    hover_data=['task_count', 'completed_count'],
                    color_discrete_sequence=px.colors.sequential.Viridis  # Исправлено: убрали color_continuous_scale
                )
                fig1.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Выручка: %{value:,.0f} ₽<br>Задач: %{customdata[0]}<br>Выполнено: %{customdata[1]}<extra></extra>'
                )
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("💰 Установите стоимость этапов для анализа выручки")
            
            # 2. Горизонтальная гистограмма трудозатрат
            st.subheader("Трудозатраты по этапам")
            
            # Сортируем по трудозатратам
            sorted_df = project_analytics.sort_values('total_actual_hours', ascending=True)
            
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                y=sorted_df['stage_name'],
                x=sorted_df['total_actual_hours'],
                name='Фактические часы',
                orientation='h',
                marker_color='#e74c3c',
                text=sorted_df['total_actual_hours'].round(1),
                textposition='auto'
            ))
            
            fig2.add_trace(go.Bar(
                y=sorted_df['stage_name'],
                x=sorted_df['total_planned_hours'],
                name='Плановые часы',
                orientation='h',
                marker_color='#3498db',
                text=sorted_df['total_planned_hours'].round(1),
                textposition='auto'
            ))
            
            fig2.update_layout(
                title='Трудозатраты по этапам',
                xaxis_title='Часы',
                yaxis_title='Этапы',
                barmode='overlay',
                hovermode='y unified',
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # 3. Scatter plot: стоимость vs трудозатрат
            st.subheader("Соотношение стоимости и трудозатрат")
            
            if len(project_analytics) > 1:
                fig3 = px.scatter(
                    project_analytics,
                    x='total_actual_hours',
                    y='stage_cost',
                    size='task_count',
                    color='stage_name',
                    hover_name='stage_name',
                    hover_data=['completed_count', 'avg_efficiency'],
                    title='Соотношение стоимости этапов и трудозатрат',
                    labels={
                        'total_actual_hours': 'Фактические часы',
                        'stage_cost': 'Стоимость (₽)',
                        'stage_name': 'Этап',
                        'task_count': 'Количество задач'
                    },
                    size_max=40
                )
                
                # Добавляем линию тренда
                fig3.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')))
                fig3.update_layout(showlegend=True, legend_title="Этапы")
                
                st.plotly_chart(fig3, use_container_width=True)
            
            # Статистика проекта
            total_planned_hours = project_analytics['total_planned_hours'].sum()
            total_actual_hours = project_analytics['total_actual_hours'].sum()
            total_tasks = project_analytics['task_count'].sum()
            completed_tasks = project_analytics['completed_count'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Этапов", len(project_analytics))
            with col2:
                st.metric("Выручка", f"{total_revenue:,.0f} ₽")
            with col3:
                st.metric("Задачи", f"{completed_tasks}/{total_tasks}")
            with col4:
                efficiency = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                st.metric("Выполнение", f"{efficiency:.1f}%")
            
            # Таблица с данными
            display_df = project_analytics[['stage_name', 'stage_cost', 'task_count', 
                                          'completed_count', 'total_planned_hours', 
                                          'total_actual_hours']].copy()
            display_df['completion_rate'] = (display_df['completed_count'] / display_df['task_count'].replace(0, 1) * 100).round(1)
            display_df.columns = ['Этап', 'Стоимость (₽)', 'Задач', 'Выполнено', 
                                'План. часы', 'Факт. часы', 'Выполнение %']
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("📝 В проекте нет данных для анализа")
    
    # ВКЛАДКА 3: Отклонения от плана
    with tab3:
        project_analytics = db.get_project_analytics(project_id)
        
        if not project_analytics.empty:
            # Фильтруем этапы с данными
            filtered_df = project_analytics[
                (project_analytics['total_planned_hours'] > 0) | 
                (project_analytics['total_actual_hours'] > 0)
            ].copy()
            
            if not filtered_df.empty:
                # Рассчитываем отклонения
                filtered_df['deviation_hours'] = filtered_df['total_actual_hours'] - filtered_df['total_planned_hours']
                
                # Исправляем деление на ноль
                filtered_df['deviation_percent'] = filtered_df.apply(
                    lambda row: (row['deviation_hours'] / row['total_planned_hours'] * 100) 
                    if row['total_planned_hours'] > 0 else 0,
                    axis=1
                )
                
                # 1. Waterfall chart отклонений
                st.subheader("Суммарные отклонения от плана")
                
                fig1 = go.Figure(go.Waterfall(
                    name="Отклонения",
                    orientation="v",
                    measure=["relative"] * len(filtered_df),
                    x=filtered_df['stage_name'],
                    y=filtered_df['deviation_hours'],
                    textposition="outside",
                    text=[f"{d:.1f} ч" for d in filtered_df['deviation_hours']],
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    increasing={"marker": {"color": "#e74c3c"}},  # красный для опозданий
                    decreasing={"marker": {"color": "#2ecc71"}},  # зеленый для опережений
                ))
                
                fig1.update_layout(
                    title="Отклонения от плана по этапам",
                    showlegend=False,
                    xaxis_title="Этапы",
                    yaxis_title="Отклонение (часы)",
                    hovermode='x',
                    height=500
                )
                
                st.plotly_chart(fig1, use_container_width=True)
                
                # 2. Групповая гистограмма плана и факта
                st.subheader("План vs Факт по этапам")
                
                fig2 = go.Figure()
                
                fig2.add_trace(go.Bar(
                    x=filtered_df['stage_name'],
                    y=filtered_df['total_planned_hours'],
                    name='Плановые часы',
                    marker_color='#3498db',
                    text=filtered_df['total_planned_hours'].round(1),
                    textposition='auto'
                ))
                
                fig2.add_trace(go.Bar(
                    x=filtered_df['stage_name'],
                    y=filtered_df['total_actual_hours'],
                    name='Фактические часы',
                    marker_color='#e74c3c',
                    text=filtered_df['total_actual_hours'].round(1),
                    textposition='auto'
                ))
                
                fig2.update_layout(
                    title='Сравнение плановых и фактических часов',
                    xaxis_title='Этапы',
                    yaxis_title='Часы',
                    barmode='group',
                    hovermode='x unified',
                    showlegend=True
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # 3. Heatmap отклонений
                st.subheader("Тепловая карта отклонений")
                
                # Создаем матрицу для heatmap
                filtered_df['deviation_category'] = filtered_df['deviation_hours'].apply(
                    lambda x: 'Опережение' if x < 0 else ('Задержка' if x > 0 else 'По плану')
                )
                
                category_order = ['Опережение', 'По плану', 'Задержка']
                filtered_df['deviation_category'] = pd.Categorical(
                    filtered_df['deviation_category'], 
                    categories=category_order, 
                    ordered=True
                )
                
                # Группируем по категориям
                heatmap_data = filtered_df.groupby('deviation_category').agg({
                    'stage_name': 'count',
                    'deviation_hours': 'sum'
                }).reset_index()
                
                fig3 = px.bar(
                    heatmap_data,
                    x='deviation_category',
                    y='stage_name',
                    color='deviation_hours',
                    title='Распределение этапов по категориям отклонений',
                    color_continuous_scale='RdYlGn_r',  # Красный-Желтый-Зеленый (обратный)
                    labels={'stage_name': 'Количество этапов', 'deviation_category': 'Категория отклонения'}
                )
                
                fig3.update_layout(
                    xaxis_title="Категория отклонения",
                    yaxis_title="Количество этапов",
                    coloraxis_colorbar=dict(title="Суммарное отклонение (ч)")
                )
                
                st.plotly_chart(fig3, use_container_width=True)
                
                # Статистика
                total_deviation = filtered_df['deviation_hours'].sum()
                avg_deviation = filtered_df['deviation_hours'].mean()
                ontime_stages = len(filtered_df[filtered_df['deviation_hours'] == 0])
                ahead_stages = len(filtered_df[filtered_df['deviation_hours'] < 0])
                behind_stages = len(filtered_df[filtered_df['deviation_hours'] > 0])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Суммарное отклонение", f"{total_deviation:.1f} ч")
                with col2:
                    st.metric("Среднее отклонение", f"{avg_deviation:.1f} ч")
                with col3:
                    st.metric("Этапов впереди плана", ahead_stages)
                with col4:
                    st.metric("Этапов с задержкой", behind_stages)
                
                # Таблица
                display_df = filtered_df[['stage_name', 'total_planned_hours', 
                                        'total_actual_hours', 'deviation_hours', 
                                        'deviation_percent']].copy()
                display_df.columns = ['Этап', 'План. часы', 'Факт. часы', 
                                    'Отклонение (часы)', 'Отклонение %']
                display_df = display_df.round(1)
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("📊 Нет данных о плановых и фактических часах")
        else:
            st.info("📝 В проекте нет данных для анализа отклонений")
    
    # ВКЛАДКА 4: Эффективность сотрудников
    with tab4:
        # Получаем данные о производительности
        performance_df = db.get_employee_performance(
            st.session_state.analytics_filters['start_date'].strftime('%Y-%m-%d'),
            st.session_state.analytics_filters['end_date'].strftime('%Y-%m-%d')
        )
        
        # Получаем данные о зарплатах
        salaries_df = db.get_all_salaries()
        
        if not performance_df.empty:
            # Объединяем с данными о зарплатах
            if not salaries_df.empty:
                latest_salaries = salaries_df.sort_values('month').groupby('user_id').last().reset_index()
                merged_df = pd.merge(
                    performance_df,
                    latest_salaries[['user_id', 'salary_amount']],
                    on='user_id',
                    how='left'
                )
                merged_df['salary_amount'] = merged_df['salary_amount'].fillna(0)
            else:
                merged_df = performance_df.copy()
                merged_df['salary_amount'] = 0
            
            # Рассчитываем метрики
            merged_df['efficiency_score'] = (merged_df['avg_efficiency'].fillna(0) * 100).round(1)
            merged_df['productivity'] = (merged_df['total_actual_hours'] / merged_df['total_planned_hours'].replace(0, 1) * 100).round(1)
            
            # 1. Пузырьковая диаграмма эффективности
            st.subheader("Эффективность сотрудников")
            
            fig1 = px.scatter(
                merged_df,
                x='total_actual_hours',
                y='efficiency_score',
                size='salary_amount',
                color='full_name',
                hover_name='full_name',
                hover_data=['total_tasks', 'completed_tasks', 'ontime_tasks', 'salary_amount'],
                title='Эффективность сотрудников (размер пузырька = зарплата)',
                labels={
                    'total_actual_hours': 'Фактические часы',
                    'efficiency_score': 'Эффективность (%)',
                    'full_name': 'Сотрудник',
                    'salary_amount': 'Зарплата (₽)'
                },
                size_max=60
            )
            
            # Добавляем средние линии
            avg_hours = merged_df['total_actual_hours'].mean()
            avg_efficiency = merged_df['efficiency_score'].mean()
            
            fig1.add_hline(y=avg_efficiency, line_dash="dash", line_color="gray", 
                          annotation_text=f"Средняя: {avg_efficiency:.1f}%")
            fig1.add_vline(x=avg_hours, line_dash="dash", line_color="gray",
                          annotation_text=f"Среднее: {avg_hours:.1f} ч")
            
            fig1.update_layout(
                showlegend=True,
                legend_title="Сотрудники",
                hovermode='closest',
                height=500
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
            # 2. Radar chart для сравнения сотрудников
            st.subheader("Сравнение сотрудников по ключевым метрикам")
            
            # Подготавливаем данные для radar chart
            radar_metrics = ['efficiency_score', 'productivity', 'completed_tasks', 'ontime_tasks']
            radar_df = merged_df[['full_name'] + radar_metrics].copy()
            
            # Нормализуем значения от 0 до 100
            for metric in radar_metrics:
                max_val = radar_df[metric].max()
                if max_val > 0:
                    radar_df[metric] = (radar_df[metric] / max_val * 100).round(1)
            
            # Создаем radar chart для каждого сотрудника
            fig2 = go.Figure()
            
            for _, employee in radar_df.iterrows():
                fig2.add_trace(go.Scatterpolar(
                    r=employee[radar_metrics].tolist(),
                    theta=['Эффективность', 'Продуктивность', 'Выполнено', 'В срок'],
                    name=employee['full_name'],
                    fill='toself'
                ))
            
            fig2.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                title="Сравнение сотрудников по ключевым метрикам",
                showlegend=True,
                height=500
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # 3. Горизонтальная гистограмма зарплат и эффективности
            st.subheader("Зарплаты и эффективность")
            
            # Сортируем по зарплате
            salary_df = merged_df.sort_values('salary_amount', ascending=True)
            
            fig3 = go.Figure()
            
            fig3.add_trace(go.Bar(
                y=salary_df['full_name'],
                x=salary_df['salary_amount'],
                name='Зарплата',
                orientation='h',
                marker_color='#3498db',
                text=salary_df['salary_amount'].round(0),
                textposition='auto'
            ))
            
            fig3.add_trace(go.Scatter(
                y=salary_df['full_name'],
                x=salary_df['efficiency_score'] * salary_df['salary_amount'].max() / 100,
                name='Эффективность',
                mode='markers+text',
                marker=dict(size=12, color='#e74c3c'),
                text=salary_df['efficiency_score'],
                textposition='middle right'
            ))
            
            fig3.update_layout(
                title='Зарплаты и эффективность сотрудников',
                xaxis_title="Зарплата (₽) / Эффективность (шкала)",
                yaxis_title="Сотрудники",
                barmode='overlay',
                hovermode='y unified',
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
            # 4. Расчет финансовых метрик
            st.subheader("Финансовые метрики сотрудников")
            
            work_days_per_month = 22
            work_hours_per_month = work_days_per_month * 8
            
            metrics_data = []
            for _, emp in merged_df.iterrows():
                emp_salary = emp.get('salary_amount', 0)
                actual_hours = emp.get('total_actual_hours', 0)
                
                # Рассчитываем метрики
                avg_day_earnings = emp_salary / work_days_per_month if work_days_per_month > 0 and emp_salary > 0 else 0
                avg_hour_earnings = emp_salary / work_hours_per_month if work_hours_per_month > 0 and emp_salary > 0 else 0
                company_hour_cost = emp_salary / actual_hours if actual_hours > 0 and emp_salary > 0 else 0
                
                # ROI сотрудника (предполагаем выручку = часы * 1000 руб/час)
                revenue_per_hour = 1000  # примерная ставка
                employee_revenue = actual_hours * revenue_per_hour
                roi = ((employee_revenue - emp_salary) / emp_salary * 100) if emp_salary > 0 else 0
                
                metrics_data.append({
                    'Сотрудник': emp['full_name'],
                    'Зарплата (₽)': f"{emp_salary:,.0f}" if emp_salary > 0 else "Не указана",
                    'Ср. заработок/день': f"{avg_day_earnings:,.0f} ₽" if avg_day_earnings > 0 else "—",
                    'Ср. заработок/час': f"{avg_hour_earnings:,.0f} ₽" if avg_hour_earnings > 0 else "—",
                    'Стоимость часа': f"{company_hour_cost:,.0f} ₽" if company_hour_cost > 0 else "—",
                    'Факт. часы': f"{actual_hours:.1f}",
                    'Эффективность': f"{emp.get('efficiency_score', 0):.1f}%",
                    'ROI': f"{roi:.1f}%" if emp_salary > 0 else "—"
                })
            
            metrics_df = pd.DataFrame(metrics_data)
            st.dataframe(metrics_df, use_container_width=True, height=400)
            
            # Форма для добавления зарплат
            with st.expander("💰 Управление зарплатами", expanded=False):
                users_df = db.get_all_users()
                non_admin_users = users_df[users_df['login'] != 'admin']
                
                if not non_admin_users.empty:
                    with st.form("add_salary_form"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            user_options = {row['full_name']: row['user_id'] for _, row in non_admin_users.iterrows()}
                            selected_user = st.selectbox("Сотрудник", list(user_options.keys()))
                        
                        with col2:
                            salary_month = st.date_input(
                                "Месяц",
                                value=date.today().replace(day=1)
                            )
                        
                        with col3:
                            salary_amount = st.number_input(
                                "Зарплата (₽)",
                                min_value=0.0,
                                value=50000.0,
                                step=1000.0
                            )
                        
                        if st.form_submit_button("💾 Сохранить зарплату"):
                            user_id = user_options[selected_user]
                            db.add_salary(
                                user_id, 
                                salary_month.strftime('%Y-%m-%d'), 
                                salary_amount
                            )
                            st.success(f"✅ Зарплата для {selected_user} сохранена")
                            st.rerun()
        else:
            st.info("📊 Нет данных о производительности сотрудников за выбранный период")

# Информация о данных
st.markdown("---")
with st.expander("ℹ️ Информация о расчетах"):
    st.write("""
    **Методика расчетов:**
    
    1. **Эффективность:** Плановые часы / Фактические часы × 100%
    2. **Продуктивность:** Фактические часы / Плановые часы × 100%
    3. **Стоимость задачи:** (Часы задачи / Сумма часов этапа) × Стоимость этапа
    4. **ROI сотрудника:** (Выручка - Зарплата) / Зарплата × 100%
    5. **Выручка сотрудника:** Фактические часы × 1000 руб/час (примерная ставка)
    6. **Отклонение:** Фактические часы - Плановые часы
    7. **Положительное отклонение:** Фактические часы > Плановые часы (задержка)
    8. **Отрицательное отклонение:** Фактические часы < Плановых часов (опережение)
    """)