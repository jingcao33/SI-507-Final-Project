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


def get_ranks(sort_by, sort_order):
    conn = sqlite3.connect('sf_restaurants.sqlite')
    cur = conn.cursor()

    if sort_by == 'ratings':
        q = f'''
        SELECT name, rating
        FROM business
		ORDER BY rating {sort_order}
		LIMIT 10
        '''
    elif sort_by == 'review_counts':
        q = f'''
        SELECT name, review_count
        FROM business
		ORDER BY review_count {sort_order}
		LIMIT 10
        '''
    else:
        q = f'''
        SELECT business_name, inspection_score
        FROM Inspection
		ORDER BY inspection_score {sort_order}
		LIMIT 10
        '''

    # print(q)
    ranks = cur.execute(q).fetchall()
    conn.close()
    return ranks


def get_info(rest_name):
    conn = sqlite3.connect('sf_restaurants.sqlite')
    cur = conn.cursor()

    q = '''
    SELECT b.name, i.business_address, b.zipcode,
    b.phone, b.is_closed, i.inspection_score, b.rating
    FROM business b
    JOIN inspection i
    ON b.name=i.business_name
    AND b.zipcode= i.business_zipcode

    '''

    info = cur.execute(q).fetchall()
    conn.close()
    return info


def get_complaint(complaint):
    if complaint == 'general':
        r = ('Environmental Health', main.eh_contact, main.eh_website)
    elif complaint == 'severe':
        r = ('Disease Control', main.dc_contact, main.dc_website)
    else:
        r = ('City Customer Service Agency', main.cp_contact, main.cp_website)
    return r

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/category', methods=['POST'])
def restaurants():
    source_cat = request.form['category']
    results = get_results(source_cat)

    return render_template('category.html',
                            results=results,
                           category=source_cat)


@app.route('/evaluation', methods=['POST'])
def evaluation():
    sort_by = request.form['sort']
    sort_order = request.form['dir']

    ranks = get_ranks(sort_by, sort_order)

    x_vals = [r[0] for r in ranks]
    y_vals = [r[1] for r in ranks]
    eval_data = go.Bar(
        x=x_vals,
        y=y_vals
    )
    fig = go.Figure(data=eval_data)
    div = fig.to_html(full_html=False)
    return render_template('evaluation.html', plot_div=div)


@app.route('/info', method=['POST'])
def info():
    rest_name = request.form['restaurant_name']
    info = get_info(rest_name)
    return render_template('info.html', results=info)


@app.route('/complaint', method=['POST'])
def complaint():
    complaint = request.form['complaint']
    contact_info = get_complaint(complaint)
    return render_template('complaint.html', results=contact_info)


if __name__ == '__main__':
    app.run(debug=True)
