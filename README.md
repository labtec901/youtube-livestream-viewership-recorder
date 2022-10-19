# youtube-livestream-viewership-recorder
Record, log, and graph the live concurrent viewership of a YouTube Livestream
![starbase-live-24-7-starship-super-heavy-development-from-spacex-s-boca-chica-facility_graph](https://user-images.githubusercontent.com/11169730/196594217-e2a9e274-ede7-4654-a69b-7fbd919b1950.png)

```
usage: main.py [-h] [-gshow] [-gsave] url [r] [api_key]

positional arguments:
  url         A YouTube livestream URL
  r           How often to fetch and log viewership (sec) (default: just once)
  api_key     Youtube API Key (default: hardcoded)

options:
  -h, --help  show this help message and exit
  -gshow      Graph and show the CSV output
  -gsave      Graph and save a PNG of the CSV output
  ```
