# Wikidata Query API (CKG)

A simplified version of https://www.wikidata.org/w/api.php.

## Run service

```
pip install -r requirements.txt
python service.py
```

## Instructions

Supported parameters:

```
action=query
list=search
format=json
uselang=en,ru,... (defaults to en)
srsearch=query keyword
srlimit=10 (defaults to 10)
```

Returns:
```
{
  "query": {
    "searchinfo": {
      "totalhits": 1 // total hits
    },
    "search": [
      {
        "title": "Q7808399", // QNode
        "snippet": [
          "West Indian cricketer" // This snippet will be in the language that "uselang" specifies. If no such language, then English will be used. If no English, a random language snippet returns. 
        ]
      }
    ]
  }
}
```
