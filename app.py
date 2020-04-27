from flask import Flask, render_template, request
import sqlite3
import main
import plotly.graph_objects as go

app = Flask(__name__)


def get_results(source_cat):
    conn = sqlite3.connect('sf_restaurants.sqlite')
    cur = conn.cursor()

    where_clause = ''
    if (source_cat != 'All'):
        where_clause = f'WHERE c.name = "{source_cat}"'

    q = f'''
        SELECT b.name, b.is_closed, b.price
        FROM Business b
        JOIN Categories cat
        ON b.id=cat.business_id
        JOIN Cat c
        ON cat.cat_id=c.id
		{where_clause}
		ORDER BY RANDOM()
		LIMIT 10
    '''
    # print(q)
    results = cur.execute(q).fetchall()
    conn.close()
    # print(results)
    return results


def get_ranks():
    conn = sqlite3.connect('sf_restaurants.sqlite')
    cur = conn.cursor()

    sort_by = request.form['sort']
    sort_order = request.form['dir']
    
    if sort_by == 'ratings':
        sort_column = 'b.rating'
    elif sort_by == 'review_counts':
        sort_column = 'b.review_count'
    else:
        sort_column = 'i.inspection_score'

    # where_clause = ''
    # if (source_cat != 'All'):
    #     where_clause = f'WHERE c.name = "{source_cat}"'

    q = f'''
        SELECT b.name, b.is_closed, b.price
        FROM Business b
        JOIN Categories cat
        ON b.id=cat.business_id
        JOIN Cat c
        ON cat.cat_id=c.id
		ORDER BY RANDOM()
		LIMIT 10
    '''
    print(q)
    ranks = cur.execute(q).fetchall()
    conn.close()
    return ranks


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/category', methods=['POST'])
def restaurants():
    source_cat = request.form['category']
    results = get_results(source_cat)

    return render_template('results.html',
                            results=results,
                           category=source_cat)


@app.route('/evaluation', methods=['POST'])
def evaluation():
    sort_by = request.form['sort']
    sort_order = request.form['dir']

    rerults = get_ranks(sort_by, sort_order)

    x_vals = [r[0] for r in results]
    y_vals = [r[1] for r in results]
    eval_data = go.Bar(
        x=x_vals,
        y=y_vals
    )
    fig = go.Figure(data=eval_data)
    div = fig.to_html(full_html=False)
    return render_template('evaluation.html', plot_div=div)




if __name__ == '__main__':
    app.run(debug=True)
