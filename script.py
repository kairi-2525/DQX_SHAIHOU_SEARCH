import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import subprocess
import os
from bs4 import BeautifulSoup
import re
from tkinter import font

def toggle_row_selection(event):
    """ダブルクリックで行の選択状態をトグルする"""
    item = output_table.identify_row(event.y)
    if item:
        if item in selected_rows:
            update_selected_rows(item, False)
            output_table.item(item, tags=())
        else:
            update_selected_rows(item, True)
            output_table.item(item, tags=("selected",))

def update_selected_rows(item, selected):
    """選択された行のリストを更新する"""
    if selected and item not in selected_rows:
        selected_rows.append(item)
    elif not selected and item in selected_rows:
        selected_rows.remove(item)
    update()

# レシピの詳細を分割して素材と数を抽出する関数
def extract_materials(recipe_details):
    # 正規表現パターンを定義
    pattern = r"[○◯]([^○◯]+?)×(\d+)"
    
    # 正規表現パターンにマッチする部分を抽出
    matches = re.findall(pattern, recipe_details)
    
    # 抽出したデータを辞書に格納
    materials = {}
    for match in matches:
        item_name = match[0]
        quantity = int(match[1])  # 数量を数値に変換
        materials[item_name] = quantity
    return materials

# ソートの状態を管理する変数を追加
sort_order = {"item_count": False, "recipe_name": False, "craftsman_level": False, "item_name": False, "recipe_details": False, "acquisition_method": False}
last_use_col = "item_count"

def resort():
    sort_column(last_use_col, False)

def sort_column(col, toggled):
    """列をクリックしたときのソート関数"""
    last_use_col = col
    # ソートの状態を取得
    current_sort_order = sort_order[col]
    
    if toggled:
        # ソート順をトグル
        current_sort_order = sort_order[col] = not current_sort_order
    
    # 選択された行と選択されていない行を分離
    selected_data = [(output_table.set(child, col), child) for child in selected_rows]
    unselected_data = [(output_table.set(child, col), child) for child in output_table.get_children('') if child not in selected_rows]

    # 数値としてソート
    selected_data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else x[0], reverse=current_sort_order)
    unselected_data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else x[0], reverse=current_sort_order)

    # 選択された行と選択されていない行を結合
    combined_data = selected_data + unselected_data

    # 結合されたリストに基づいて行を並べ替え
    for index, (val, child) in enumerate(combined_data):
        output_table.move(child, '', index)

item_quantity_entries = {}

def fetch_data():
    # ここにデータ取得のロジックを入れる
    global selected_rows

    # 選択された行のリストをリセット
    selected_rows = []

    item_quantity_entries = {}

    output_text.delete(1.0, tk.END)  # テキストボックスの内容をクリア
    output_text.insert(tk.INSERT, "データを取得中...\n")
    # テーブルをクリア
    for child in output_table.get_children():
        output_table.delete(child)

    url = 'https://dragon-quest.jp/ten/recipe/saihou.php'
    filename = "filename.html"

    # wgetコマンドを実行
    subprocess.run(["curl", url, "-o", filename])

    # ファイルを開く
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    # ファイルを削除
    os.remove(filename)

    # HTMLを解析
    soup = BeautifulSoup(content, 'html.parser')

    # ページ内の全てのテーブルを検索
    tables = soup.find_all('table', {'class': 'ta1_sk mb15'})
    item_count = 0
    for table in tables:
        # テーブルの行を抽出
        rows = table.find_all('tr')

        # rowspanを管理するための変数
        current_recipe_name = None
        current_acquisition_method = None

        # データ行が始まるまでの行数をカウントする
        skip_rows = 2  # ヘッダ行と見出し行をスキップする
        current_row = 0

        for row in rows:
            current_row += 1
            # 指定された行数だけスキップ
            if current_row <= skip_rows:
                continue

            cols = row.find_all('td')
            cols_text = [ele.text.strip() for ele in cols]

            # 変数の初期化
            item_count = item_count + 1
            recipe_name = current_recipe_name  # 前の行の値を引き継ぐ
            craftsman_level = "none"
            item_name = "none"
            recipe_details = "none"
            acquisition_method = current_acquisition_method  # 前の行の値を引き継ぐ


            # 各行の列の数に応じて処理を分岐
            # 各行の列の数に応じて処理を分岐
            if len(cols_text) == 5:
                # 新しいレシピの開始
                recipe_name, craftsman_level, item_name, recipe_details, acquisition_method = cols_text
                current_recipe_name = recipe_name  # 現在のレシピ名を更新
                current_acquisition_method = acquisition_method  # 現在の入手方法を更新
            elif len(cols_text) == 4:
                # レシピ名と入手方法が継続
                craftsman_level, item_name, recipe_details = cols_text
                recipe_name = current_recipe_name
                acquisition_method = current_acquisition_method
            elif len(cols_text) == 3:
                # レシピ名のみ継続
                craftsman_level, item_name, recipe_details = cols_text
                recipe_name = current_recipe_name
                # 入手方法は前の行から引き継ぎ
                acquisition_method = current_acquisition_method
            elif len(cols_text) == 1:
                # 例外的な行（例：カテゴリーヘッダーなど）
                continue  # この行をスキップ
            else:
                # 他の予期しないフォーマット
                print(f"予期しないフォーマットの行: {cols_text}")
                continue  # この行をスキップ
            
            craftsman_level = craftsman_level.replace("Lv", "")
            recipe_details = extract_materials(recipe_details)

            # 各要素を表示
            print("No.", item_count)
            print("レシピ名:", recipe_name)
            print("職人レベル:", craftsman_level)
            print("アイテム名:", item_name)
            print("レシピの詳細:", recipe_details)
            print("入手方法:", acquisition_method)
            output = f"No.: {item_count}\nレシピ名: {recipe_name}\n職人レベル: {craftsman_level}\nアイテム名: {item_name}\nレシピの詳細: {recipe_details}\n入手方法: {acquisition_method}\n\n"
            
            # テーブルにデータを追加
            data = [item_count, recipe_name, craftsman_level, item_name, recipe_details, acquisition_method]
            output_table.insert("", "end", values=data)

            output_text.insert(tk.INSERT, output)
            # テキストボックスのスクロールを最下部に移動
            output_text.see(tk.END)
            # root.update_idletasks()  # 画面の更新を強制
            

    output_text.insert(tk.INSERT, "データを取得完了\n")
    # テキストボックスのスクロールを最下部に移動
    output_text.see(tk.END)
    update_selected_items_display()
    calculate_totals()

current_search_query = ''

def on_search_entry_changed(event=None):
    global current_search_query
    current_search_query = search_entry.get().lower()
    update_result_listbox()
    matching_items = []

def on_result_selected(event):
    # 選択されたリストボックスの項目を取得
    selected_index = result_listbox.curselection()
    if not selected_index:
        return
    selected_text = result_listbox.get(selected_index)
    print(selected_text)
    # Treeviewのアイテムをループして一致するものを探す
    for child in output_table.get_children():
        if output_table.item(child, 'values')[3] == selected_text:
            # 選択状態をトグル
            if child in selected_rows:
                selected_rows.remove(child)
                output_table.item(child, tags=())
            else:
                selected_rows.append(child)
                output_table.item(child, tags=("selected",))
            update()
            break

def update_result_listbox():
    result_listbox.delete(0, tk.END)  # 現在のリストボックスの内容をクリア
    if current_search_query != '':
        for child in output_table.get_children():
            item_text = output_table.item(child, 'values')[3]  # 3はカラムインデックス
            if current_search_query in item_text.lower():
                result_listbox.insert(tk.END, item_text)
                
                # 選択された行であれば強調表示
                if child in selected_rows:
                    result_listbox.itemconfig(result_listbox.size() - 1, {'bg': 'lightgray'})

def validate_quantity_input(P):
    if P == "" or (P.isdigit() and int(P) > 0):
        return True
    else:
        return False

def on_quantity_changed(item_name):
    # 数量が変更されたアイテム名を受け取り、合計を再計算
    calculate_totals()

def update_selected_items_display():
    # 現在のselected_items_frameにあるウィジェットを確認し、不要なものを削除
    for item_name, widgets in list(item_quantity_entries.items()):
        label, quantity_entry = widgets
        if item_name not in [output_table.item(child, 'values')[3] for child in selected_rows]:
            # selected_rowsに含まれないアイテムのウィジェットを削除
            label.destroy()
            quantity_entry.destroy()
            # item_quantity_entriesからも削除
            del item_quantity_entries[item_name]

    for index, child in enumerate(selected_rows):
        item_name = output_table.item(child, 'values')[3]  # 'item_name' カラムの値

        if item_name in item_quantity_entries:
            # 既存のウィジェットを再配置
            label, quantity_entry = item_quantity_entries[item_name]
        else:
            # 新しいウィジェットを作成
            label = tk.Label(selected_items_frame, text=f"{item_name}", borderwidth=2, relief=tk.GROOVE)
            quantity_entry = tk.Entry(selected_items_frame, validate="key", borderwidth=2, relief=tk.GROOVE)
            validate_func = selected_items_frame.register(validate_quantity_input)
            quantity_entry.configure(validatecommand=(validate_func, "%P"))
            quantity_entry.insert(0, "1")  # 初期値を1に設定

            # item_quantity_entries 辞書を更新
            item_quantity_entries[item_name] = (label, quantity_entry)

        # ウィジェットを配置
        label.grid(row=index, column=0, sticky='nsew')
        quantity_entry.grid(row=index, column=1, sticky='nsew')
        
        # エントリーにイベントハンドラをバインド
        quantity_entry.bind('<KeyRelease>', lambda event, name=item_name: on_quantity_changed(name))

    # グリッドの行と列のサイズを調整
    selected_items_frame.grid_columnconfigure(0, weight=3)
    selected_items_frame.grid_columnconfigure(1, weight=1)

def calculate_totals():
    # フレーム内のウィジェットをクリア
    for widget in selected_items_frame2.winfo_children():
        widget.destroy()
    
    total_quantities = {}  # 合計数量を格納する辞書

    for child in selected_rows:
        item_name = output_table.item(child, 'values')[3]  # アイテム名
        label, quantity_entry = item_quantity_entries[item_name]
        quantity = int(quantity_entry.get())  # 入力された個数
        recipe_details = output_table.item(child, 'values')[4]  # recipe_details

        # recipe_details から各素材と数量を抽出して合計する
        for material, material_quantity in eval(recipe_details).items():
            if material not in total_quantities:
                total_quantities[material] = 0
            total_quantities[material] += material_quantity * quantity

    # 合計を表示
    count = 0
    bold_font = font.Font(family="Helvetica", size=12, weight="bold")
    for material, quantity in total_quantities.items():
        #print(f"{material}: {quantity}")
        label = tk.Label(selected_items_frame2, text=f"{material}: {quantity}個", font=bold_font, borderwidth=2, relief=tk.GROOVE)
        label.grid(row=count, column=0, sticky='nsew')
        count += 1


def update():
    update_result_listbox()  # リストボックスの表示を更新
    resort()
    update_selected_items_display()
    calculate_totals()

def toggle_textbox():
    if output_text.winfo_viewable():
        output_text.grid_forget()  # テキストボックスを非表示にする
        toggle_button.config(text="デバッグ情報を表示")
    else:
        output_text.grid(row=main_row, column=0, sticky='nsew', padx=10, pady=10)  # テキストボックスを再表示する
        toggle_button.config(text="デバッグ情報を隠す")

root = tk.Tk()
root.title("データ取得アプリ")

main_row = 0

# 表を表示するフレームの作成と配置
table_frame = tk.Frame(root)
table_frame.grid(row=main_row, column=0, sticky='nsew')
root.grid_rowconfigure(0, weight=2)  # 表のフレームには2の重みを設定
root.grid_columnconfigure(0, weight=1)  # 列に重みを設定
main_row += 1

# 表の作成とフレームへの追加
output_table = ttk.Treeview(table_frame, selectmode='none', columns=("item_count", "recipe_name", "craftsman_level", "item_name", "recipe_details", "acquisition_method"), show="headings")
output_table.grid(row=0, column=0, sticky='nsew')  # gridを使用してフレーム内に配置

# Treeviewにイベントハンドラをバインド
output_table.bind("<Double-1>", toggle_row_selection)

# ヘッダーをクリックしたときにソート関数を呼び出すように設定
output_table.heading("item_count", text="No.", command=lambda: sort_column("item_count", True))
output_table.heading("recipe_name", text="レシピ名", command=lambda: sort_column("recipe_name", True))
output_table.heading("craftsman_level", text="職人レベル", command=lambda: sort_column("craftsman_level", True))
output_table.heading("item_name", text="アイテム名", command=lambda: sort_column("item_name", True))
# output_table.heading("recipe_details", text="レシピの詳細", command=lambda: sort_column("recipe_details", True))
# output_table.heading("acquisition_method", text="入手方法", command=lambda: sort_column("acquisition_method", True))
output_table.heading("recipe_details", text="レシピの詳細")
output_table.heading("acquisition_method", text="入手方法")
output_table.tag_configure("selected", background="lightgray")  # 背景色を設定

table_frame.grid_rowconfigure(0, weight=1)  # Treeviewに重みを設定
table_frame.grid_columnconfigure(0, weight=1)  # 列に重みを設定

button_frame = tk.Frame(root)
button_frame.grid(row=main_row, column=0, sticky='nsew', padx=5, pady=5)
main_row += 1

toggle_button = tk.Button(button_frame, text="デバッグ情報を表示", command=toggle_textbox)
toggle_button.grid(row=0, column=0, sticky='ew', pady=5)

# データ取得ボタンの設定と配置
fetch_button = tk.Button(button_frame, text="データ取得", command=fetch_data)
fetch_button.grid(row=0, column=1, sticky='ew', pady=10)

search_and_result_frame = tk.Frame(root)
search_and_result_frame.grid(row=main_row, column=0, sticky='nsew', padx=5, pady=5)
main_row += 1
# ウィンドウのグリッド設定を更新
search_and_result_frame.grid_rowconfigure(0, weight=1)
search_and_result_frame.grid_columnconfigure(0, weight=1)  # 既存の列
search_and_result_frame.grid_columnconfigure(1, weight=1)  # 既存の列
search_and_result_frame.grid_columnconfigure(2, weight=1)  # 新しい列

# 検索用フレームの配置
search_frame = tk.Frame(search_and_result_frame, borderwidth=2, relief=tk.GROOVE)
search_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
header_frame = tk.Label(search_frame, text="検索", borderwidth=2, relief=tk.GROOVE)
header_frame.pack(fill=tk.BOTH, expand=True)

search_entry = tk.Entry(search_frame)
search_entry.pack(fill=tk.BOTH, expand=True)
search_entry.bind('<KeyRelease>', on_search_entry_changed)

# 検索結果表示用リストボックスの配置
result_listbox = tk.Listbox(search_frame)
result_listbox.pack(fill=tk.BOTH, expand=True)
result_listbox.bind('<Double-1>', on_result_selected)

search_frame.grid_rowconfigure(0, weight=1)
search_frame.grid_rowconfigure(1, weight=1)
search_frame.grid_rowconfigure(2, weight=9)

# リザルトフレームの作成
result_frame = tk.Frame(search_and_result_frame, borderwidth=2, relief=tk.GROOVE)
result_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
result_frame.grid_columnconfigure(0, weight=9)
result_frame.grid_columnconfigure(1, weight=1)
result_frame2 = tk.Frame(search_and_result_frame, borderwidth=2, relief=tk.GROOVE)
result_frame2.grid(row=0, column=2, sticky='nsew', padx=5, pady=5)
result_frame2.grid_columnconfigure(0, weight=9)
result_frame2.grid_columnconfigure(1, weight=1)

# ヘッダーフレームの作成
header_frame = tk.Frame(result_frame)
header_frame.grid(row=0, column=0, sticky='nsew')
header_frame.grid_columnconfigure(0, weight=3)  # アイテム名のカラムの幅を指定
header_frame.grid_columnconfigure(1, weight=1)  # 個数のカラムの幅を指定

header_frame2 = tk.Frame(result_frame2)
header_frame2.grid(row=0, column=0, sticky='nsew')
header_frame2.grid_columnconfigure(0, weight=4)  # 必要素材のカラムの幅を指定

# ヘッダーラベルの配置
header_label1 = tk.Label(header_frame, text='アイテム名', borderwidth=2, relief=tk.GROOVE)
header_label1.grid(row=0, column=0, sticky='nsew')

header_label2 = tk.Label(header_frame, text='個数', borderwidth=2, relief=tk.GROOVE)
header_label2.grid(row=0, column=1, sticky='nsew')

bold_font = font.Font(family="Helvetica", size=12, weight="bold")
header_label3 = tk.Label(header_frame2, text='必要素材', font=bold_font, borderwidth=2, relief=tk.GROOVE)
header_label3.grid(row=0, column=0, sticky='nsew')

# Canvasとスクロールバーの設定
canvas = tk.Canvas(result_frame)
scrollbar = tk.Scrollbar(result_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.grid(row=1, column=0, sticky="nsew")
canvas.grid_columnconfigure(0, weight=4)
scrollbar.grid(row=1, column=1, sticky="nse")

canvas2 = tk.Canvas(result_frame2)
scrollbar2 = tk.Scrollbar(result_frame2, orient="vertical", command=canvas.yview)
canvas2.configure(yscrollcommand=scrollbar.set)
canvas2.grid(row=1, column=0, sticky="nsew")
canvas2.grid_columnconfigure(0, weight=4)
scrollbar2.grid(row=1, column=1, sticky="nse")

# 選択されたアイテム表示用フレームの配置
selected_items_frame = tk.Frame(canvas)
selected_items_frame.grid(row=0, column=0, rowspan=2, sticky='nsew')
def on_frame_configure(event):
    # スクロール領域をフレームのサイズに合わせて更新
    canvas.configure(scrollregion=canvas.bbox("all"))
selected_items_frame.bind("<Configure>", on_frame_configure)
selected_items_frame.grid_columnconfigure(0, weight=3)
selected_items_frame.grid_columnconfigure(1, weight=1)

# 選択されたアイテム表示用フレームの配置
selected_items_frame2 = tk.Frame(canvas2)
selected_items_frame2.grid(row=0, column=0, rowspan=2, sticky='nsew')
def on_frame_configure2(event):
    # スクロール領域をフレームのサイズに合わせて更新
    canvas2.configure(scrollregion=canvas2.bbox("all"))
selected_items_frame2.bind("<Configure>", on_frame_configure2)
selected_items_frame2.grid_columnconfigure(0, weight=4)

# テキストボックスの作成と配置
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD)
output_text.grid(row=main_row, column=0, sticky='nsew', padx=10, pady=10)
output_text.grid_forget()
main_row += 1

# ウィンドウのグリッド設定
root.grid_rowconfigure(0, weight=9)
root.grid_rowconfigure(1, weight=9)
root.grid_rowconfigure(2, weight=9)
root.grid_rowconfigure(3, weight=9)

root.mainloop()