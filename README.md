# youtube-livestream-viewership-recorder
Record, log, and graph the live concurrent viewership of a YouTube Livestream
![starbase-live-24-7-starship-super-heavy-development-from-spacex-s-boca-chica-facility_graph](https://user-images.githubusercontent.com/11169730/196594217-e2a9e274-ede7-4654-a69b-7fbd919b1950.png)

```
usage: main.py [-h] [--filepath [FILEPATH]] [--api_key [API_KEY]] [-gshow] [-gsave] url [r]

Log viewership for a youtube livestream

positional arguments:
  url                   A YouTube livestream URL
  r                     How often to fetch and log viewership (sec) (default: just once)

options:
  -h, --help            show this help message and exit
  --filepath [FILEPATH] Path to save logs and images to (default: current working directory)
  --api_key [API_KEY]   Youtube API Key (default: hardcoded)
  -gshow                Graph and show the CSV output
  -gsave                Graph and save a PNG of the CSV output
  ```
