import json
import flask

# from flask import Flask


from scrapegraphai.graphs import SmartScraperGraph

from custom_class.smart_scraper_grapg import MySmartScraperGraph

app = flask.Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return "hello"


@app.route('/api/v0/get_content', methods=['GET'])
def get_content():
    question = flask.request.args.get('question')
    source = flask.request.args.get('source')
    data = test(source, question)
    return json.dumps(data, indent=2)


def test(source, question):
    graph_config = {
        "llm": {
            "api_key": "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",
            "model": "gpt-3.5-turbo"
        },
        "verbose": True,
        "headless": False
    }
    smart_scraper_graph = MySmartScraperGraph(
        prompt=question,
        source=source,
        config=graph_config
    )
    result = smart_scraper_graph.run()
    return result


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
