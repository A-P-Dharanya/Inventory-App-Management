from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
import io
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'inventory.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with open('schema.sql', 'r') as f:
        conn = get_db()
        conn.executescript(f.read())
        conn.commit()
        conn.close()

@app.route('/')
def home():
    conn = get_db()
    products = conn.execute('SELECT * FROM products').fetchall()
    locations = conn.execute('SELECT * FROM locations').fetchall()
    movements = conn.execute('SELECT * FROM movements ORDER BY timestamp DESC LIMIT 5').fetchall()

    stock_data = {product['product_id']: {location['location_id']: 0 for location in locations} for product in products}

    for movement in conn.execute('SELECT * FROM movements'):
        product_id = movement['product_id']
        qty = movement['qty']
        from_location = movement['from_location']
        to_location = movement['to_location']

        if from_location:
            stock_data[product_id][from_location] -= qty
        if to_location:
            stock_data[product_id][to_location] += qty

    conn.close()
    return render_template('home.html', products=products, locations=locations, stock_data=stock_data, movements=movements)

@app.route('/products')
def view_products():
    conn = get_db()
    products = conn.execute('SELECT * FROM products').fetchall()
    locations = conn.execute('SELECT * FROM locations').fetchall()

    stock_data = {product['product_id']: {location['location_id']: 0 for location in locations} for product in products}

    for movement in conn.execute('SELECT * FROM movements'):
        product_id = movement['product_id']
        qty = movement['qty']
        from_location = movement['from_location']
        to_location = movement['to_location']

        if from_location:
            stock_data[product_id][from_location] -= qty
        if to_location:
            stock_data[product_id][to_location] += qty

    conn.close()
    return render_template('products.html', products=products, locations=locations, stock_data=stock_data)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['name']
        type_ = request.form['type']
        description = request.form['description']
        condition = request.form['condition']
        price = float(request.form['price'])

        conn = get_db()
        try:
            conn.execute('INSERT INTO products (product_id, name, type, description, condition, price) VALUES (?, ?, ?, ?, ?, ?)',
                         (product_id, name, type_, description, condition, price))
            conn.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('view_products'))
        except sqlite3.Error as e:
            conn.rollback()
            flash(f'Error adding product: {e}', 'error')
        finally:
            conn.close()
    return render_template('add_product.html')

@app.route('/products/edit/<id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = get_db()
    product = conn.execute('SELECT * FROM products WHERE product_id = ?', (id,)).fetchone()

    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('view_products'))

    if request.method == 'POST':
        name = request.form['name']
        type_ = request.form['type']
        description = request.form['description']
        condition = request.form['condition']
        price = float(request.form['price'])

        try:
            conn.execute('UPDATE products SET name = ?, type = ?, description = ?, condition = ?, price = ? WHERE product_id = ?',
                         (name, type_, description, condition, price, id))
            conn.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('view_products'))
        except sqlite3.Error as e:
            conn.rollback()
            flash(f'Error updating product: {e}', 'error')
        finally:
            conn.close()

    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<id>')
def delete_product(id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM products WHERE product_id = ?', (id,))
        conn.commit()
        flash('Product deleted successfully!', 'success')
    except sqlite3.Error as e:
        conn.rollback()
        flash(f'Error deleting product: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('view_products'))

@app.route('/locations')
def view_locations():
    conn = get_db()
    locations = conn.execute('SELECT * FROM locations').fetchall()
    conn.close()
    return render_template('locations.html', locations=locations)

@app.route('/locations/add', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        location_id = request.form['location_id']
        city = request.form['city']

        conn = get_db()
        try:
            conn.execute('INSERT INTO locations (location_id, city) VALUES (?, ?)', (location_id, city))
            conn.commit()
            flash('Location added successfully!', 'success')
            return redirect(url_for('view_locations'))
        except sqlite3.Error as e:
            conn.rollback()
            flash(f'Error adding location: {e}', 'error')
        finally:
            conn.close()
    return render_template('add_location.html')

@app.route('/locations/edit/<id>', methods=['GET', 'POST'])
def edit_location(id):
    conn = get_db()
    location = conn.execute('SELECT * FROM locations WHERE location_id = ?', (id,)).fetchone()

    if not location:
        flash('Product not found!', 'error')
        return redirect(url_for('view_locations'))

    if request.method == 'POST':
        city = request.form['city']

        try:
            conn.execute('UPDATE locations SET city = ? WHERE location_id = ?', (city, id))
            conn.commit()
            flash('Location updated successfully!', 'success')
            return redirect(url_for('view_locations'))
        except sqlite3.Error as e:
            conn.rollback()
            flash(f'Error updating location: {e}', 'error')
        finally:
            conn.close()

    return render_template('edit_location.html', location=location)

@app.route('/locations/delete/<id>')
def delete_location(id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM locations WHERE location_id = ?', (id,))
        conn.commit()
        flash('Location deleted successfully!', 'success')
    except sqlite3.Error as e:
        conn.rollback()
        flash(f'Error deleting location: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('view_locations'))

@app.route('/movements')
def view_movements():
    conn = get_db()
    movements = conn.execute('''
        SELECT m.*, p.name as product_name, 
               l1.city as from_location_name, 
               l2.city as to_location_name
        FROM movements m
        JOIN products p ON m.product_id = p.product_id
        LEFT JOIN locations l1 ON m.from_location = l1.location_id
        LEFT JOIN locations l2 ON m.to_location = l2.location_id
        ORDER BY m.timestamp DESC
    ''').fetchall()
    conn.close()
    return render_template('movements.html', movements=movements)

@app.route('/movements/add', methods=['GET', 'POST'])
def add_movement():
    conn = get_db()
    products = conn.execute('SELECT * FROM products').fetchall()
    locations = conn.execute('SELECT * FROM locations').fetchall()

    if request.method == 'POST':
        movement_id = request.form['movement_id']
        product_id = request.form['product_id']
        from_location = request.form['from_location'] or None
        to_location = request.form['to_location'] or None
        qty = int(request.form['qty'])
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Validate stock if moving from a location
        if from_location:
            # Calculate current stock at from_location
            stock = 0
            movements = conn.execute('SELECT * FROM movements WHERE product_id = ?', (product_id,)).fetchall()
            for movement in movements:
                if movement['to_location'] == from_location:
                    stock += movement['qty']
                if movement['from_location'] == from_location:
                    stock -= movement['qty']
            if stock < qty:
                conn.close()
                flash(f'Insufficient stock at {from_location}. Available: {stock}, Requested: {qty}', 'error')
                return redirect(url_for('add_movement'))

        try:
            conn.execute('INSERT INTO movements (movement_id, product_id, from_location, to_location, qty, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                         (movement_id, product_id, from_location, to_location, qty, timestamp))
            conn.commit()
            flash('Movement added successfully!', 'success')
            return redirect(url_for('view_movements'))
        except sqlite3.Error as e:
            conn.rollback()
            flash(f'Error adding movement: {e}', 'error')
        finally:
            conn.close()

    conn.close()
    return render_template('add_movement.html', products=products, locations=locations)

@app.route('/movements/edit/<id>', methods=['GET', 'POST'])
def edit_movement(id):
    conn = get_db()
    movement = conn.execute('SELECT * FROM movements WHERE movement_id = ?', (id,)).fetchone()
    products = conn.execute('SELECT * FROM products').fetchall()
    locations = conn.execute('SELECT * FROM locations').fetchall()

    if not movement:
        flash('Movement not found!', 'error')
        return redirect(url_for('view_movements'))

    if request.method == 'POST':
        product_id = request.form['product_id']
        from_location = request.form['from_location'] or None
        to_location = request.form['to_location'] or None
        qty = int(request.form['qty'])

        # Validate stock if moving from a location
        if from_location:
            # Calculate current stock at from_location, excluding the current movement
            stock = 0
            movements = conn.execute('SELECT * FROM movements WHERE product_id = ? AND movement_id != ?', (product_id, id)).fetchall()
            for m in movements:
                if m['to_location'] == from_location:
                    stock += m['qty']
                if m['from_location'] == from_location:
                    stock -= m['qty']
            if stock < qty:
                conn.close()
                flash(f'Insufficient stock at {from_location}. Available: {stock}, Requested: {qty}', 'error')
                return redirect(url_for('edit_movement', id=id))

        try:
            conn.execute('UPDATE movements SET product_id = ?, from_location = ?, to_location = ?, qty = ? WHERE movement_id = ?',
                         (product_id, from_location, to_location, qty, id))
            conn.commit()
            flash('Movement updated successfully!', 'success')
            return redirect(url_for('view_movements'))
        except sqlite3.Error as e:
            conn.rollback()
            flash(f'Error updating movement: {e}', 'error')
        finally:
            conn.close()

    conn.close()
    return render_template('edit_movement.html', movement=movement, products=products, locations=locations)

@app.route('/movements/delete/<id>')
def delete_movement(id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM movements WHERE movement_id = ?', (id,))
        conn.commit()
        flash('Movement deleted successfully!', 'success')
    except sqlite3.Error as e:
        conn.rollback()
        flash(f'Error deleting movement: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('view_movements'))

@app.route('/report')
def product_movement_report():
    conn = get_db()
    movements = conn.execute('''
        SELECT m.*, p.name as product_name, 
               l1.city as from_location_name, 
               l2.city as to_location_name
        FROM movements m
        JOIN products p ON m.product_id = p.product_id
        LEFT JOIN locations l1 ON m.from_location = l1.location_id
        LEFT JOIN locations l2 ON m.to_location = l2.location_id
        ORDER BY m.timestamp DESC
    ''').fetchall()
    conn.close()
    return render_template('product_movement_report.html', movements=movements)

@app.route('/report/download')
def download_product_movement_report():
    conn = get_db()
    movements = conn.execute('''
        SELECT m.*, p.name as product_name, 
               l1.city as from_location_name, 
               l2.city as to_location_name
        FROM movements m
        JOIN products p ON m.product_id = p.product_id
        LEFT JOIN locations l1 ON m.from_location = l1.location_id
        LEFT JOIN locations l2 ON m.to_location = l2.location_id
        ORDER BY m.timestamp DESC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Movement ID', 'Product', 'From Location', 'To Location', 'Quantity', 'Timestamp'])
    for movement in movements:
        writer.writerow([
            movement['movement_id'],
            movement['product_name'],
            movement['from_location_name'] or 'None',
            movement['to_location_name'] or 'None',
            movement['qty'],
            movement['timestamp']
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='product_movement_report.csv'
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)