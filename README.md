# project_3
____
# Приложение для прогноза погоды на заданном маршруте
+ Определение погоды реализовано на библиотеке OpenWeather из-за лучших условий по лимитам запросов. 
+ Определение местоположения реализовано через Geocoding API от проекта OpenMeteo, т. к. этот вариант при тестировании наиболее часто верно определял город
+ Интерфейс карт реализован через OpenStreetMap
+ В проекте использован кастомный CSS для отрисовки элементов интерфейса в стиле LMS :)
## Ответы на вопросы: 
- Для визуализации погодных данных лучше подходят следующие графики:
    - Линейный, т. к. на нём легче всего заметить тренды в изменении данных, также на нём хорошо видно изменение погоды с течением времени
    - Гистограмма, т. к. на ней лучше видны изменения погоды с течением времени
    - т. к. наше приложение решает задачу просмотра прогноза погоды на небольшом временном периоде, а также для большей интуитивности, в нём реализовано отображение только линейных графиков
- Улучшение пользовательского опыта:
    - Дополнительная информация о конкретной точке на графике при наведении курсора
    - Изменение масштаба графика
    - Выбор отображения определённых типов данных на графике
    - Дополнительные анимации на графиках
