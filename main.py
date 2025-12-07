cars = [

    {
      "id": 3648,
      "name": "Спринтер Груз_01KG616AQ",
      "fuel": None,
      "lat": 42.6966399,
      "lon": 74.2469633
    },
    {
      "id": 3642,
      "name": "Хово_01KG622AQ",
      "fuel": 162.33,
      "lat": 42.8329166,
      "lon": 74.6501666
    },
    {
      "id": 3641,
      "name": "Спринтер КУБЫ",
      "fuel": 74.19,
      "lat": 42.8437849,
      "lon": 74.5859333
    }
]

for i in cars:
    if i['fuel'] is None:
        continue
    print(i)