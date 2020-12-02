from flask import Flask, render_template, request, json, jsonify
import pymysql
import requests
app = Flask(__name__)

table_list = []
column_list = []

def db_access(db_name, sql_query):
    conn = pymysql.connect(host='localhost',
                           user='ItsukiNagao',
                           passwd='nagaoitsuki',
                           db='%s' % (db_name),
                           charset='utf8',
                           cursorclass=pymysql.cursors.DictCursor
                           )
    try:
        with conn.cursor() as cursor:
            sql = "%s" % (sql_query)
            cursor.execute(sql)
            result = cursor.fetchall()
    finally:
        conn.close()
    return result

user_id = "Itsuki-0129"

login_flag = 0

if login_flag == 1:
    login_info = user_id
else:
    login_info = "ログイン"

#ホームページ
@app.route('/', methods = ["GET", "POST"])
def index():
    return render_template("index.html", login_info=login_info)

@app.route('/ajax_db', methods=["GET", "POST"])
def ajax_001():
    selected_db = request.json['select_db']
    table_list.clear()
    for i in db_access(str(selected_db), str("show tables;")):
        print(i["Tables_in_" + str(selected_db)])
        table_list.append(i["Tables_in_" + str(selected_db)])

    json_for_js = []
    for h in table_list:
        json_for_js.append({"tables": h})

    return jsonify(json_for_js)

@app.route('/ajax_table', methods=["GET", "POST"])
def ajax_002():
    selected_db = request.json['select_db']
    selected_table = request.json['select_table']
    column_list.clear()
    for i in db_access(str(selected_db), str("show columns from " + selected_table + ";")):
        print(i["Field"])
        column_list.append(i["Field"])
    json_for_checkbox = []
    for h in column_list:
        json_for_checkbox.append({"columns": h})
    print("/ajax_tableのjsonifyの値は、"+str(json_for_checkbox))
    return jsonify(json_for_checkbox)

@app.route('/ajax_column', methods=["GET", "POST"])
def ajax_003():
    selected_db = request.json['select_db']
    selected_table = request.json['select_table']
    selected_columns = request.json['check_001']
    test_search_word = request.json['text_001']
    sql_query = "select "+", ".join(str(e) for e in selected_columns)+" from "+str(selected_table)+" where "+" or ".join(str(e)+" like '%"+test_search_word+"%'" for e in selected_columns)+";"
    print("●クエリはこちら→"+"("+sql_query+")")
    db_result = db_access(selected_db, sql_query)
    print("db_resultをまるごと表示→"+str(db_result))
    return jsonify(db_result)

#会員登録ページ
@app.route('/register', methods = ["GET", "POST"])
def register_form():
    return render_template("register.html", login_info=login_info)

#ログインページ
@app.route('/login', methods = ["GET", "POST"])
def login_form():
    return render_template("login.html", login_info=login_info)

#検索ページ
@app.route('/search', methods = ["GET", "POST"])
def search_form():
    db_result = db_access("", "show databases;")
    db_list = []
    for i in db_result:
        db_list.append(i["Database"])
    return render_template("search.html", db_list=db_list, login_info=login_info)

#共有ページ
@app.route('/upload', methods = ["GET", "POST"])
def pptx_upload():
    return render_template("upload.html", login_info=login_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)