# Mission Tree Generator

Generates mission trees for games.

## Features

- Missions groupable by part/questline
- Per tag styling
- Extendable with custom extractor classes

## Usage

1. Extract the data:

```shell
missiontreegen extract --extractor rdr --output-file missions.json
```

2. Create a style (optional)

```json
{
  "default": {
    "background_color": "#ff0000"
  },
  "other_tag": {
    "background_color": "#00ff00"
  }
}
```

3. Generate the tree

```shell
missiontreegen generate-tree --input-file missions.json --output-file tree.png --format png --style style.json
```

## Supported Games

Below is a list of supported games. If a game is not on a list, feel free to write an extractor class and submit a pull
request.

- Red Dead Redemption
