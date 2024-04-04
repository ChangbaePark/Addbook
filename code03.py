# code02.py는 주소록 불러오기 저장하기와 삭제 하기까지 하였으며 

# Code03.py은 
# 오른쪽 버튼 메뉴 중 edit(수정) 활성화 하기 
# 수정을 위한 EditDialog Class 추가 하고 이 다이얼로그에서 입력 받은 내용을 
# MainWindow Class의 def edit_item(self):함수에서 적절히 처리 하고 화면을 리프래쉬 하기 

import sys
import shutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QLabel
from addBookMySQL import *

class EditDialog(QDialog):
    def __init__(self, name, phone, photo_path, parent=None):

        super().__init__(parent)
        self.setWindowTitle('주소록 수정')
        self.setGeometry(200, 200, 300, 320)

        # DB 객체 생성 앞으로 self.db 라는 객체로 불리게 됨.
        self.db = mysqlDB()
        print (self.db)

        self.name_label = QLabel('이름:', self)
        self.name_label.move(20, 20)
        self.name_edit = QLineEdit(self)
        self.name_edit.setGeometry(80, 20, 200, 20)
        self.name_edit.setText(name)  # 기존 이름 설정

        self.phone_label = QLabel('전화번호:', self)
        self.phone_label.move(20, 50)
        self.phone_edit = QLineEdit(self)
        self.phone_edit.setGeometry(80, 50, 200, 20)
        self.phone_edit.setText(phone)  # 기존 전화번호 설정

        self.photo_button = QPushButton('사진 선택', self)
        self.photo_button.setGeometry(20, 80, 100, 30)
        self.photo_button.clicked.connect(self.select_photo)
        
        self.photo_label = QLabel(self)
        self.photo_label.setGeometry(140, 80, 200, 200)
        # 기존 사진이 있는 경우에는 해당 사진을 표시합니다.
        if photo_path:
            pixmap = QPixmap(photo_path)
            self.photo_label.setPixmap(pixmap)
            self.photo_label.setScaledContents(True)
            self.photo_path = photo_path
        else:
            self.photo_path = None

        self.save_button = QPushButton('저장', self)
        self.save_button.setGeometry(20, 280, 100, 30)
        self.save_button.clicked.connect(self.save_changes)

        self.cancel_button = QPushButton('취소', self)
        self.cancel_button.setGeometry(140, 280, 100, 30)
        self.cancel_button.clicked.connect(self.reject)

    def select_photo(self):
        filename, _ = QFileDialog.getOpenFileName(self, '이미지 파일 선택', '', '이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif)')
        if filename:
            pixmap = QPixmap(filename)
            pixmap = pixmap.scaled(200, 200)
            self.photo_label.setPixmap(pixmap)
            self.photo_path = filename  # 파일 경로를 저장합니다.

    def save_changes(self):
        name = self.name_edit.text()
        phone = self.phone_edit.text()
        photo_path = self.photo_path  # 선택된 사진의 경로를 가져옵니다.
        print (f'name{name} - phone{phone} path{photo_path}')

        if name and phone:            
            self.accept()  # 다이얼로그를 닫고 변경사항을 저장합니다.                        
            return name, phone, photo_path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()        
        loadUi('./res/ui01.ui', self)

        # DB 객체 생성 앞으로 self.db
        self.db = mysqlDB()
        print (self.db)

        self.setWindowTitle('내가 만드는 주소록 Ver 0.1')        
        self.image_paths = [] # 이미지 파일의 경로를 저장하는 변수를 초기화합니다.
        
        self.empty_pixmap = QPixmap() # 빈 이미지를 생성합니다.
        self.default_pixmap = QPixmap('./res/unknown.png')  # 디폴트 이미지 경로        
        
        self.load_address_book() # 실행시 주소록 읽어 오기
        
        self.pushButton.clicked.connect(self.open_image_dialog)        
        self.pushButton_3.clicked.connect(self.save_address_book)        
        self.lineEdit.returnPressed.connect(self.add_to_address_book)        
        self.pushButton_4.clicked.connect(self.add_to_address_book)
        self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        # 컨텍스트 메뉴를 생성합니다.
        context_menu = QMenu()
        delete_action = QAction("삭제", self)
        delete_action.triggered.connect(self.delete_item)
        context_menu.addAction(delete_action)

        # 수정 액션을 추가합니다.
        edit_action = QAction("수정", self)
        edit_action.triggered.connect(self.edit_item)
        context_menu.addAction(edit_action)

        # 컨텍스트 메뉴를 보여줍니다.
        context_menu.exec_(self.listWidget.mapToGlobal(pos))

    def delete_item(self):
        # 선택된 아이템을 화면에서 삭제합니다.
        selected_items = self.listWidget.selectedItems()

        # 복사본을 만들어 반복문을 돌면서 삭제합니다.
        for item in selected_items.copy():
            row = self.listWidget.row(item)
            self.listWidget.takeItem(row)
            # 화면에서 삭제된 아이템의 인덱스를 이용하여 서버에서도 해당 정보를 삭제합니다.
            self.db.delete(item.text().split(' - ')[0])
 
    # Edit 버튼 클릭 시 실행되는 메서드
    def edit_item(self):
        # 선택된 아이템을 가져옵니다.
        selected_items = self.listWidget.selectedItems()

        # 선택된 아이템이 없는 경우에는 아무것도 하지 않습니다.
        if not selected_items:
            return

        # 첫 번째 선택된 아이템을 가져옵니다.
        selected_item = selected_items[0]
        index = self.listWidget.row(selected_item)
        name, phone = selected_item.text().split(' - ')
        photo_path = self.image_paths[index]  # 해당 아이템의 이미지 파일 경로를 가져옵니다.

        # EditDialog를 생성하고 실행합니다.
        edit_dialog = EditDialog(name, phone, photo_path, parent=self)
        if edit_dialog.exec_() == QDialog.Accepted:
            # 수정 다이얼로그에서 저장 버튼이 눌렸을 때의 처리를 합니다.
            new_name, new_phone, new_photo_path = edit_dialog.save_changes()
            selected_item.setText(f"{new_name} - {new_phone}")
            if new_photo_path:
                pixmap = QPixmap(new_photo_path)
            else:
                pixmap = self.default_pixmap
            selected_item.setIcon(QIcon(pixmap))
            self.image_paths[index] = new_photo_path

            # 데이터베이스 업데이트
            self.db.update(name, new_phone, new_photo_path)

        # 주소록을 리프레시합니다.
        self.refresh_address_book()
                
    def refresh_address_book(self):
        print("Refreshing address book...")  # 디버깅 메시지 추가
        # 선택된 아이템을 가져옵니다.
        selected_items = self.listWidget.selectedItems()
        for item in selected_items:
            # 현재 선택된 아이템의 인덱스를 가져옵니다.
            index = self.listWidget.row(item)
            # 수정된 이름과 전화번호를 가져옵니다.
            new_name, new_phone = item.text().split(' - ')
            # # 수정된 사진 경로를 가져옵니다.
            new_photo_path = self.image_paths[index]
            # 현재 아이템의 정보를 가져옵니다.
            current_name, current_phone = self.get_item_info(item)
            # 만약 수정 다이얼로그에서 새로운 이름과 전화번호가 입력되었다면
            if new_name != current_name or new_phone != current_phone:
                # 수정된 텍스트로 아이템을 업데이트합니다.
                new_text = f'{new_name} - {new_phone}'
                item.setText(new_text)
                # 수정된 사진 경로로 아이콘을 업데이트합니다.
                if new_photo_path != "None":
                    pixmap = QPixmap(new_photo_path)
                else:
                    pixmap = self.default_pixmap
                item.setIcon(QIcon(pixmap))
        print("Address book refreshed.")  # 디버깅 메시지 추가

    def get_item_info(self, item):
        # 주어진 QListWidgetItem에서 이름과 전화번호를 추출합니다.
        text = item.text()
        name, phone = text.split(' - ')
        return name, phone

    def load_address_book(self):
        addresses = self.db.read_address_book()
        for address in addresses:
            name = address['name']
            phone = address['phone']
            # 이미지 경로를 가져오는 부분 수정
            photo_path = address.get('filename', 'res/unknown.png')  # 사진 경로가 없는 경우 기본 이미지를 사용
            self.add_to_list_widget(name, phone, photo_path)

   
    def add_to_list_widget(self, name, phone, photo_path):
        item = QListWidgetItem(f"{name} - {phone}")

        # 이미지 파일의 경로가 비어 있거나 None이라면 기본 이미지를 설정합니다.
        if not photo_path or photo_path.strip().lower() == 'none':
            pixmap = self.default_pixmap
        else:
            # 이미지 파일의 경로가 존재한다면 해당 경로의 이미지를 로드합니다.
            pixmap = QPixmap(photo_path)
            
        item.setIcon(QIcon(pixmap))

        # QListWidget에 item을 추가합니다.
        self.listWidget.addItem(item)
        
        # 이미지 파일의 경로를 저장합니다.
        self.image_paths.append(photo_path)

    def save_address_book(self):
        filename = 'addbook2.csv'        
        # 만약 사용자가 파일을 선택했다면
        if filename:
            # listWidget의 아이템을 파일에 저장합니다.
            with open(filename, 'w') as file:
                for index in range(self.listWidget.count()):
                    item = self.listWidget.item(index)
                    # 아이템에서 이름과 전화번호를 가져옵니다.
                    name, phone = item.text().split(' - ')                    
                    # 아이콘의 파일 경로를 가져옵니다.                    
                    photo_path = self.image_paths[index]  # 해당 아이템의 이미지 파일 경로를 가져옵니다.
                    # 이름, 전화번호, 이미지 파일 경로를 파일에 씁니다.
                    file.write(name + ',' + phone + ',' + photo_path + '\n')
            # 주소록을 저장했다는 메시지를 표시합니다.
            QMessageBox.information(self, '주소록 저장', '주소록이 성공적으로 저장되었습니다.')

    def add_to_address_book(self):
        # lineEdit에 입력된 텍스트를 가져옵니다.
        name = self.lineEdit.text().strip()
        phone = self.lineEdit_2.text().strip()
        photo_path = self.label_4.text().strip()

        # 가져온 데이터가 비어있지 않은 경우에만 주소록에 추가합니다.
        if name and phone:
            # QListWidgetItem을 생성합니다.
            item = QListWidgetItem(name + ' - ' + phone)

            # 사진이 있는 경우에는 해당 사진을 표시하고, 없는 경우에는 빈 이미지를 표시합니다.
            if photo_path.strip().lower() != 'none':
                pixmap = QPixmap(photo_path)
            else:
                pixmap = self.empty_pixmap

            # QListWidgetItem에 아이콘을 설정합니다.
            item.setIcon(QIcon(pixmap))

            # QListWidget에 item을 추가합니다.
            self.listWidget.addItem(item)
            
            # 이미지 파일의 경로를 저장합니다.
            self.image_paths.append(photo_path)

            #Data Base에 넣기
            # __init__ 에서 db = mysqlDB()로 만들어진 객체를 이용
            result = self.db.insert(name, phone, photo_path)
            print("Insert test: ", result)   

            # lineEdit을 초기화합니다.
            self.lineEdit.clear()
            self.lineEdit_2.clear()

    def open_image_dialog(self):
        # 파일 다이얼로그를 엽니다.
        filename, _ = QFileDialog.getOpenFileName(self, '이미지 파일 선택', '', '이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif)')

        # 만약 사용자가 파일을 선택했다면
        if filename:
            # 선택한 이미지 파일을 label_3에 표시합니다.
            pixmap = QPixmap(filename)
            self.label_3.setPixmap(pixmap)
            self.label_3.setScaledContents(True)
            self.label_4.setText(filename)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
