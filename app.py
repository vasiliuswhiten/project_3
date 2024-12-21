import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import openmeteo_requests
import requests_cache
from retry_requests import retry
import requests

# Настройки API
# Настройки API
API_KEY = "311009e731663fbf64196b1959691d08"
BASE_URL_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"
GEOCODE_URL = "http://api.openweathermap.org/geo/1.0/direct"

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Получение координат по городу и запись в переменные
def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()

        if "results" in data and len(data["results"]) > 0:
            latitude = data["results"][0]["latitude"]
            longitude = data["results"][0]["longitude"]
            return latitude, longitude
        else:
            raise ValueError(f"Не удалось найти координаты для города: {city}")

    except requests.exceptions.RequestException:
        raise ConnectionError("Ошибка подключения к серверу.")
    except ValueError as ve:
        raise ve


def get_weather_data(city):
    """Получение погодных данных для одного города."""
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'
    }
    try:
        response = requests.get(BASE_URL_FORECAST, params=params, timeout=5)
        response.raise_for_status()
        forecast_data = response.json()
        return forecast_data['list']  # Возвращаем список прогнозов
    except Exception as e:
        print(f"Ошибка получения данных для {city}: {e}")
        return []

# Ваши функции get_weather_data и get_coordinates остаются без изменений

# Инициализация Dash приложения
app = dash.Dash(__name__)
app.title = "Маршрутный прогноз погоды"

# Основной макет приложения
app.layout = html.Div([
    html.H1("Прогноз погоды для маршрута", style={'textAlign': 'center'}),

    # Ввод точек маршрута
    html.Div([
        html.Label("Введите точки маршрута:"),
        dcc.Input(id='start-point', type='text', placeholder="Начальная точка", style={'marginRight': '10px'}),
        dcc.Input(id='end-point', type='text', placeholder="Конечная точка", style={'marginRight': '10px'}),
        html.Button('Добавить промежуточную точку', id='add-stop-btn', n_clicks=0),
        html.Div(id='intermediate-stops', children=[], style={'marginTop': '10px'})
    ], style={'marginBottom': '20px'}),

    # Выбор временного интервала и параметра
    html.Div([
        html.Label("Выберите параметры прогноза:"),
        dcc.Dropdown(
            id='parameter-dropdown',
            options=[
                {'label': 'Температура', 'value': 'temp'},
                {'label': 'Скорость ветра', 'value': 'wind'},
                {'label': 'Осадки', 'value': 'rain'}
            ],
            value=['temp'],  # Сделаем значение списком по умолчанию для multi=True
            multi=True
        ),
        dcc.RadioItems(
            id='interval-selector',
            options=[
                {'label': '1 день', 'value': 1},
                {'label': '3 дня', 'value': 3},
                {'label': '5 дней', 'value': 5}
            ],
            value=1,
            inline=True
        )
    ], style={'marginBottom': '20px'}),

    # Кнопка для обновления данных
    html.Button('Получить прогноз', id='submit-btn', n_clicks=0),

    # Карта маршрута
    html.Div([
        html.H3("Маршрут на карте"),
        dcc.Graph(id='map-graph', style={'height': '500px'})
    ], style={'marginTop': '20px'}),

    # Графики с прогнозом
    html.Div(id='weather-output')
])


# Callback для добавления промежуточных точек маршрута
@app.callback(
    Output('intermediate-stops', 'children'),
    [Input('add-stop-btn', 'n_clicks')],
    [State('intermediate-stops', 'children')]
)
def add_intermediate_stop(n_clicks, children):
    if n_clicks > 0:
        new_input = dcc.Input(
            type='text',
            placeholder=f"Промежуточная точка {len(children) + 1}",
            id={'type': 'stop', 'index': len(children)},
            style={'marginRight': '10px', 'marginTop': '5px'}
        )
        children.append(new_input)
    return children



# Callback для обновления карты и графиков
@app.callback(
    [Output('map-graph', 'figure'),
     Output('weather-output', 'children')],
    [Input('submit-btn', 'n_clicks')],
    [State('start-point', 'value'),
     State('end-point', 'value'),
     State('intermediate-stops', 'children'),
     State('parameter-dropdown', 'value'),
     State('interval-selector', 'value')]
)
def update_map_and_weather(n_clicks, start, end, stops, parameters, interval):
    if n_clicks == 0 or not start or not end:
        return go.Figure(), "Введите точки маршрута и нажмите 'Получить прогноз'."

    # Собираем маршрут
    route = [start] + [child['props']['value'] for child in stops if child['props']['value']] + [end]
    map_markers = []
    weather_data = {}
    latitudes = []
    longitudes = []
    cities_display = []

    # Получаем данные для каждой точки маршрута
    for city in route:
        lat, lon = get_coordinates(city)
        if lat is None or lon is None:
            continue
        forecasts = get_weather_data(city)[:8 * interval]  # Прогноз на выбранное число дней
        if not forecasts:
            continue
        weather_data[city] = forecasts
        latitudes.append(lat)
        longitudes.append(lon)
        cities_display.append(city)

    # Создаем карту с помощью Plotly
    map_fig = go.Figure()

    # Добавляем маркеры
    map_fig.add_trace(go.Scattermapbox(
        lat=latitudes,
        lon=longitudes,
        mode='markers+lines',
        marker=go.scattermapbox.Marker(
            size=14
        ),
        text=cities_display,
        hoverinfo='text',
        name='Маршрут'
    ))

    # Настройки карты
    map_fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=5,
        mapbox_center={"lat": latitudes[0], "lon": longitudes[0]},
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    # Формируем графики для каждого города
    elements = []
    for city, forecasts in weather_data.items():
        times = [item['dt_txt'] for item in forecasts]
        traces = []  # Список данных для каждого параметра
        for param in parameters:
            if param == 'temp':
                values = [item['main']['temp'] for item in forecasts]
                y_label = 'Температура (°C)'
            elif param == 'wind':
                values = [item['wind']['speed'] for item in forecasts]
                y_label = 'Скорость ветра (м/с)'
            elif param == 'rain':
                values = [item.get('rain', {}).get('3h', 0) for item in forecasts]
                y_label = 'Осадки (мм)'
            else:
                continue  # Пропускаем неизвестные параметры

            # Добавляем данные параметра в общий график города
            traces.append(go.Scatter(
                x=times,
                y=values,
                mode='lines+markers',
                name=param.capitalize(),
                hoverinfo='x+y'
            ))

        # Добавляем график города в общий список
        elements.append(dcc.Graph(
            figure={
                'data': traces,
                'layout': go.Layout(
                    title=f"Прогноз для {city}",
                    xaxis_title="Время",
                    yaxis_title="Значения",
                    template="plotly",
                    hovermode='closest',
                    legend_title="Параметры"
                )
            }
        ))

    if not elements:
        elements.append("Нет доступных данных для отображения.")


    return map_fig, elements


# Запуск приложения
if __name__ == '__main__':
    app.run_server(debug=False)
