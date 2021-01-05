from flask import Flask, session, abort, json, jsonify, send_from_directory
from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename
import pymysql, requests, os, sys, re, datetime

app = Flask(__name__)
app.secret_key = "hogehoge"

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

def db_insert(db_name, sql_query):
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
        conn.commit()
    finally:
        conn.close()
    return "Done!"

def login_check():
    login_info = None
    if not session.get('logged_in'):
        login_info = "ログイン"
    else:
        login_info = session['user_name']
    return login_info

#ホームページ
@app.route('/', methods = ["GET", "POST"])
def index():
    login_info = login_check()
    return render_template("index.html", login_info=login_info)

#管理者データベース操作画面
@app.route('/admin', methods = ["GET", "POST"])
def admin_ctrl():
    login_info = login_check()
    db_result = db_access("", "show databases;")
    db_list = []
    for i in db_result:
        db_list.append(i["Database"])
    return render_template("admin_select.html", db_list=db_list, login_info=login_info)

#Ajaxでデータベース選択時のテーブル一覧送信
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

#Ajaxでテーブル選択時のカラム一覧送信
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

#Ajaxでカラム選択時のデータベース結果送信
@app.route('/ajax_column', methods=["GET", "POST"])
def ajax_003():
    selected_db = request.json['select_db']
    selected_table = request.json['select_table']
    selected_columns = request.json['check_001']
    test_search_word = request.json['text_001']
    sql_query = "select "+", "\
        .join(str(e) for e in selected_columns)\
            +" from "+str(selected_table)+" where "\
                +" or ".join(str(e)+" like '%"+test_search_word\
                    +"%'" for e in selected_columns)+";"
    print("●クエリはこちら→"+"("+sql_query+")")
    db_result = db_access(selected_db, sql_query)
    print("db_resultをまるごと表示→"+str(db_result))
    return jsonify(db_result)

#会員登録ページ
@app.route('/register', methods = ["GET", "POST"])
def register_form():
    login_info = login_check()
    return render_template("register.html", login_info=login_info)

#登録内容確認ページ
@app.route('/register_check', methods = ["GET", "POST"])
def register_check():
    login_info = login_check()
    mail_str = request.form['mail_str']
    user_str = request.form['user_str']
    passwd_str = request.form['password_str']

    Already = ""
    validation_message = mail_validation(mail_str)

    if validation_message == True:
        sql_query = "select count(*) from member where user ='%s' or mail = '%s';"%(user_str, mail_str)
        print("クエリは"+sql_query)
        db_result = db_access(str('final_research'), sql_query)
        print("これが問い合わせ結果→"+str(db_result[0]['count(*)']))
        if db_result[0]['count(*)'] != 0:
            Already = "そのユーザーは既に存在しています"
        else:
            Already = "登録しました！"
            #dbにinsert
            print("dbにinsert")
            sql_query = "insert into member (mail, user, password) values('%s', '%s', '%s');"%(mail_str, user_str, passwd_str)
            db_insert("final_research", sql_query)
        validation_error = ""
    else:
        validation_error = "メールアドレスの形式ではありません"
    

    return render_template("register.html", login_info=login_info\
        , Already=Already, MailAddress=mail_str, UserName=user_str, PassWord=passwd_str\
            , validation_message=validation_error)

#バリデーション判定用の関数(入力したメールアドレス)
def mail_validation(mail_address):
    #メールアドレスの形式である
    error_message = True
    result = re.fullmatch(r'^[0-9a-zA-Z_\.]+@([0-9a-zA-Z])+\.([0-9a-zA-Z\.])+([0-9a-zA-Z])+$', mail_address)

    if result is None:
        #メールアドレスの形式になっていない
        error_message = False
    elif len(re.sub(r"\.+", ".",mail_address)) != len(mail_address):
        # . が連続されているため、メールアドレスの形式になっていない
        error_message = False
    return error_message

#ログインページ
@app.route('/login', methods = ["GET", "POST"])
def login_form():
    login_info = login_check()
    return render_template("login.html", login_info=login_info)

@app.route('/re_login', methods = ["GET", "POST"])
def home():
    user_str = request.form['username']
    passwd_str = request.form['password']
    sql_query = "select count(*) from member where user = '%s' and password = '%s';"%(user_str, passwd_str)
    print(sql_query)
    db_result = db_access(str('final_research'), sql_query)
    print(db_result[0]['count(*)'])
    

    if db_result[0]["count(*)"] == 1:
        session['logged_in'] = True
        session['user_name'] = user_str
        id_query = "select id from member where user = '%s' and password = '%s';"%(user_str, passwd_str)
        id_db_result = db_access("final_research", id_query)
        print("idだけテスト→"+str(id_db_result[0]['id']))
        session['user_id'] = id_db_result[0]['id']
        
    else:
        session['logged_in'] = False
    return login_form()

#検索ページ
@app.route('/search', methods = ["GET", "POST"])
def search_form():
#----------------------------検索条件をもとに検索結果を絞る(where?)----------------------------
    #where データ名="値"の値は空でも文字列でも整数型でも""で囲めばいける？ 2020-12-18
    #とりあえずはできたけど、検索後に入力値消えるから会員登録を参考に完成させろよ
    login_info = login_check()
    select_school_type = ""
    select_subjects = ""
    select_grade = ""
    subject_title = ""
    done_year = ""
    now_page = 1
    page_limit = 5
    select_json = {'page_limit':page_limit}
    if request.method == "POST":
        select_school_type = request.form['select_school_type']#校種
        select_subjects = request.form['select_subjects']#強化領域等
        select_grade = request.form['select_grade']#学年
        subject_title = request.form['subject_title']#単元題材名
        done_year = request.form['done_year']#実施年度
        now_page = request.form['select_link']#ページネーションの現在のページ番号
        page_limit = request.form['page_limit']#ページネーションの表示件数
        select_json = {'page_limit':page_limit,'select_school_type':select_school_type, 'select_subjects':select_subjects, \
            'select_grade':select_grade, 'subject_title':subject_title, 'done_year':done_year}
        print('select_json==>'+str(select_json))
        print('ページ番号は==>'+str(now_page))
    print("これが検索条件"+select_school_type+", "+select_subjects+", "+select_grade+", "+subject_title+", "+done_year)
#-----------------------uploads_listの教材情報を表示するための準備-----------------------
    empty_box = select_school_type+select_subjects+select_grade+subject_title+done_year
    if empty_box == "":
        sql_query ="select school_type, subjects, grade, title, file_name, user_id, year from uploads_list;"
    else:
        sql_query = "select school_type, subjects, grade, title, file_name, user_id, year from uploads_list\
            where school_type='%s' or subjects='%s' or grade='%s' or title='%s' or year='%s'"%(select_school_type, select_subjects, select_grade, subject_title, done_year)
    result_uploads_list = db_access("final_research", sql_query)
    print(result_uploads_list)
    #校種リストを準備
    school_type_list = db_access("final_research", "select * from school_type;")
    #強化領域等リストを準備
    subjects_list = db_access("final_research", "select * from subjects;")
    #学年リストを準備
    grade_list = db_access("final_research", "select * from grade;")
    #ユーザー名を準備（上みたいに全部をリスト準備するとバカなので、必要なものだけを集める）
    maker_list = db_access("final_research", "select distinct user_id from uploads_list;")
    print("これが重複を除外した作成者番号"+str(maker_list))
    #重複除外作成者番号をjsonから値だけのリスト化
    user_id_list=[]
    for i in maker_list:
        user_id_list.append(i['user_id'])
    print(user_id_list)
    #keyをユーザーid、valueをユーザー名のjsonを準備
    id_name_json = [{}]
    for i in user_id_list:
        user_query = "select user from member where id = %s"%(i)
        print(db_access("final_research", user_query)[0]['user'])
        id_name_json[0].update([(i, (db_access("final_research", user_query)[0]['user']))])
    print("これがkey=id:value=username→"+str(id_name_json))
#--------------------------------------ここまで---------------------------------------
#-----------------------------------ページネーション-----------------------------------
    #page_numの中身はjsonで{ページ番号:リンク}でおk？

    #ページの最初は、=(now_page-1)*page_limit=(現在のページ-1)*表示件数
    page_start = (int(now_page)-1)*int(page_limit)

    #件数が0だと0/0でエラーが起こるので例外追加(2020-12-21)
    try:
        if len(result_uploads_list)%int(page_limit) != 0:
            page_max = len(result_uploads_list)//int(page_limit)+1
        else:
            page_max = len(result_uploads_list)//int(page_limit)
    except:
        page_max = 0
        

    #ここからはページリンク生成のテスト
    page_num = {}
    for num in range(page_max):
        page_num[num]=num

    return render_template("search.html"\
        , login_info=login_info, result_uploads_list=result_uploads_list, select_json=select_json\
            , school_type_list=school_type_list, subjects_list=subjects_list, grade_list=grade_list, id_name_json=id_name_json\
                , page_num=page_num, page_start=page_start, page_limit=page_limit, page_max=page_max, now_page=now_page)

#ファイルのアップロード先のディレクトリ
UPLOAD_FOLDER = './static/uploads'
#アップロードされるファイルの拡張子の制限
ALLOWED_EXTENSIONS = set(['pdf', 'docx', 'pptx', 'doc', 'ppt', 'txt'])
#?????
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#共有ページ
@app.route('/upload', methods = ["GET", "POST"])
def pptx_upload():
    login_info = login_check()
    try:
        print('共有ページでtry:は通過')
        #もしログインしてるなら、共有作業
        if session['logged_in'] == True:
            print("共有ページでsession['logged_in'] == Trueです")
            #↓リクエストがポスト可動科の判別
            if request.method == 'POST':
                print("共有ページでrequest.method == 'POST'です")
                #ファイルがなかった場合の処理
                if 'file' not in request.files:
                    print('ファイルがありません')
                    return redirect(request.url)
                #データの取り出し
                file = request.files['file']
                #ファイル名が無かった時の処理
                if file.filename == '':
                    print('ファイル名がありません')
                    return redirect(request.url)
                #ファイルのチェック
                if file and allwed_file(file.filename):
                    print("共有ページでfile and allwed_file(file.filename)は通過")
                    #危険な文字を削除(サニタイズ処理？)→ここで絶対パスとか消してるの？？？どうなの？？？
                    #filename = secure_filename(file.filename)
                    filename = {}
                    if os.path.isfile('./static/uploads/'+str(session['user_id'])+'/'+file.filename) == True:
                        print("共有ページでユーザーidフォルダの中にファイルがあった")
                        ex = os.path.splitext(file.filename)
                        filename['filename'] = ex[0]+'_a'+ex[1]
                        filename['url'] = '/export/%s/%s/%s'%(str(session['user_id']), str(ex[0]+'_a'+ex[1]), str(datetime.datetime.now().strftime('%H:%M:%S')))
                    else:
                        print("共有ページでユーザーidフォルダの中にファイルがなかった")
                        filename['filename'] = str(file.filename)
                        filename['url'] = '/export/%s/%s/%s'%(str(session['user_id']), str(file.filename), str(datetime.datetime.now().strftime('%H:%M:%S')))
                    print("共有ページでfilenameのjson : "+str(filename))
                    #フォルダが存在してなければフォルダを作るif文
                    if os.path.exists('./static/uploads/'+str(session['user_id']))==True:
                        print('共有ページでパスが存在!')
                    else:
                        print("共有ページでパスが存在しないからフォルダ作成")
                        #uploadsフォルダの中にユーザー名フォルダを作成
                        os.mkdir('./static/uploads/'+str(session['user_id']))
                    #-------------------------↓データベースのuploads_listに登録する-------------------------
                    select_school_type = request.form['select_school_type']
                    select_subjects = request.form['select_subjects']
                    select_grade = request.form['select_grade']
                    subject_title = request.form['subject_title']
                    done_year = request.form['done_year']
                    #↓データ名がidしかない表から値を取り出す
                    print("共有ページでユーザーid: "+str(session['user_id']))
                    #↓insertのためのカラム
                    insert_column = "file_name, user_id, school_type, subjects, grade, title, year"
                    #↓まずはただのinsertのvaluesのリスト
                    value_list = [json.dumps(filename), int(session['user_id']), int(select_school_type), int(select_subjects), int(select_grade), subject_title, done_year]
                    #↓上のvalue_listの[]がうざいので除去
                    insert_value = ", ".join(repr(e) for e in value_list)
                    print("共有ページでinsertするvaluesの中身"+", ".join(repr(e) for e in value_list))
                    #↓uploads_listテーブルにデータを登録するクエリ
                    sql_query = "insert into uploads_list (%s) values(%s)"%(insert_column, insert_value)
                    print("共有ページでinsertするsql文:"+sql_query)
                    #↓先に用意したクエリをもとにinsert
                    db_insert("final_research", sql_query)
                    #--------------------------------------↑ここまで--------------------------------------
                    #ファイルの保存
                    print("共有ページでfile.saveのパスは: "+str(app.config['UPLOAD_FOLDER'])+"/"+str(session['user_id'])+"/"+str(filename['filename']))
                    file.save(os.path.join(app.config['UPLOAD_FOLDER']+"/"+str(session['user_id']), filename['filename']))
                #アップロード後のページに転送
                return redirect(url_for('uploaded_file'))
            #アップロード画面のリターン？

            #校種リストを準備
            school_type_list = db_access("final_research", "select * from school_type;")
            #強化領域等リストを準備
            subjects_list = db_access("final_research", "select * from subjects;")
            #学年リストを準備
            grade_list = db_access("final_research", "select * from grade;")
            return render_template("upload.html", login_info=login_info, upload_status="ファイルを選択してください"\
                , school_type_list=school_type_list, subjects_list=subjects_list, grade_list=grade_list)
        else:
            #ログインしてない場合はまずログインさせる
            print("共有ページでログインしてないよ")
            return render_template("login.html", Already="共有するにはログインしてください", login_info=login_info)
    except:
        #一度もログイン作業を行なっていないとエラーになるからそのときもログインを促す
        print("共有ページでexcept:だよ")
        return render_template("login.html", Already="共有するにはログインしてください", login_info=login_info)
    #return render_template("upload.html", login_info=login_info)

@app.route('/uploads/success')
#アップロード後に転送されるページ
def uploaded_file():
    login_info = login_check()
    #return send_from_directory(app.config['UPLOAD_FOLDER']+session['user_name'], filename)
    return render_template("upload.html", login_info=login_info, upload_status="アップロードしました！")

def allwed_file(filename):
    #.があるかどうかのチェックと、拡張子の確認
    #okなら1, だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#ファイルのエクスポート
@app.route('/export/<user_id>/<file_name>/<urandom_num>')
def export_action(file_name=None, urandom_num=None, user_id=None):
    print(urandom_num)
    return send_from_directory(
        directory = './static/uploads/'+user_id,
        filename = file_name,
        as_attachment = True,
    )

#jinja2用のフィルター定義
@app.template_filter('to_json')#''で囲まれたstr扱いのjsonをjson.loadsでjsonに、つまり''をはずす。
def to_json(value):
    print(value)
    return json.loads(value)

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', port=5500, debug=True)

