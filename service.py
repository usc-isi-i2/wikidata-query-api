from config import config
import json
from flask import Flask, request, make_response
import requests

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Wikidata Query API (CKG)\n'

@app.route('/api', methods=['GET', 'POST'])
def api():
    """
    Official doc: https://www.wikidata.org/w/api.php
    """
    print(request.values)
    action = request.values['action']

    if not action:
        return make_response(json.dumps({'error':'Invalid action'}), 500)
    if action == 'query':
        return action_query(request.values)
    else:
        return make_response(json.dumps({'error':'Only "query" action is supported'}), 500)

def action_query(kwargs):
    if kwargs.get('list') != 'search':
        return make_response(json.dumps({'error':'Only "search" is supported'}), 500)

    srsearch = kwargs.get('srsearch', '')
    srlimit = kwargs.get('srlimit', 10)
    uselang = kwargs.get('uselang', 'en')

    if len(srsearch.strip()) == 0:
        return make_response(json.dumps({'error':'Invalid srsearch'}), 500)

    try:
        es_query = '''
{
  "query": {
    "bool": {
      "filter": [
        {
          "terms": {
            "namespace": [
              120
            ],
            "boost": 1.0
          }
        }
      ],
      "must_not": [
        {
          "match_phrase": {
            "descriptions.en.plain": "Wikipedia disambiguation page"
          }
        }
      ],
      "should": [
        {
          "query_string": {
            "query": "''' + srsearch + '''",
            "fields": [
              "all^0.5",
              "all.plain^1.0"
            ],
            "use_dis_max": true,
            "tie_breaker": 0.0,
            "default_operator": "and",
            "auto_generate_phrase_queries": true,
            "max_determinized_states": 10000,
            "allow_leading_wildcard": true,
            "enable_position_increments": true,
            "fuzziness": "AUTO",
            "fuzzy_prefix_length": 2,
            "fuzzy_max_expansions": 50,
            "phrase_slop": 0,
            "rewrite": "top_terms_boost_1024",
            "escape": false,
            "split_on_whitespace": true,
            "boost": 1.0
          }
        },
        {
          "multi_match": {
            "query": "''' + srsearch + '''",
            "fields": [
              "all_near_match^2.0"
            ],
            "type": "best_fields",
            "operator": "OR",
            "slop": 0,
            "prefix_length": 0,
            "max_expansions": 50,
            "lenient": false,
            "zero_terms_query": "NONE",
            "boost": 1.0
          }
        }
      ],
      "disable_coord": false,
      "adjust_pure_negative": true,
      "minimum_should_match": "1",
      "boost": 1.0
    }
  },
  "_source": {
    "includes": [
      "namespace",
      "title",
      "namespace_text",
      "wiki",
      "labels",
      "descriptions",
      "incoming_links"
    ],
    "excludes": []
  },
  "stored_fields": "text.word_count",
  "rescore": [
    {
      "window_size": 8192,
      "query": {
        "rescore_query": {
          "function_score": {
            "query": {
              "match_all": {
                "boost": 1.0
              }
            },
            "functions": [
              {
                "filter": {
                  "match_all": {
                    "boost": 1.0
                  }
                },
                "field_value_factor": {
                  "field": "incoming_links",
                  "factor": 1.0,
                  "missing": 0.0,
                  "modifier": "log2p"
                }
              },
              {
                "filter": {
                  "terms": {
                    "namespace": [
                      120
                    ],
                    "boost": 1.0
                  }
                },
                "weight": 0.2
              }
            ],
            "score_mode": "multiply",
            "max_boost": 3.4028235E+38,
            "boost": 1.0
          }
        },
        "query_weight": 1.0,
        "rescore_query_weight": 1.0,
        "score_mode": "multiply"
      }
    }
  ],
  "stats": [
    "suggest",
    "full_text",
    "full_text_querystring"
  ],
  "size": 100
}'''
        resp = requests.post('{}/{}/_search'.format(config['es_url'], config['es_index']), data=es_query)
        if resp.status_code // 100 != 2:
            return make_response(json.dumps({'error': 'ElasticSearch error', message: str(resp.content)}), 500)
        resp = json.loads(resp.content)

        ret = {
            'query': {
                'searchinfo': {'totalhits': resp['hits']['total']},
                'search': []
            }
        }
        for r in resp['hits']['hits']:
            r = r['_source']
            ret['query']['search'].append({
                'title': r['title'],
                'snippet': r['descriptions'].get(uselang) \
                    or r['descriptions'].get('en') \
                    or r['descriptions'].popitem()
            })

        return make_response(json.dumps(ret), 200)
    except Exception as e:
        # raise e
        return make_response(json.dumps({'error':'Invalid request', 'message': str(e)}), 500)

if __name__ == '__main__':
    app.run(host=config['host'], port=config['port'], threaded=True, debug=False)
