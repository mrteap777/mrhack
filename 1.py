import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QInputDialog, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from sqlalchemy import create_engine, Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class RoleSprav(Base):
    __tablename__ = 'role_sprav'
    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), nullable=False)

class SkillsSprav(Base):
    __tablename__ = 'skills_sprav'
    skills_id = Column(Integer, primary_key=True)
    skill_name = Column(String(50), nullable=False)

class Students(Base):
    __tablename__ = 'students'
    stud_id = Column(Integer, primary_key=True)
    fname = Column(String(50), nullable=False)
    sname = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    date_reg = Column(Date)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)

class Projects(Base):
    __tablename__ = 'projects'
    project_id = Column(Integer, primary_key=True)
    p_name = Column(String(255), nullable=False)
    description = Column(String(1000), default='без описания')
    skills = Column(String(255))
    startdate = Column(Date)
    endgate = Column(Date)
    published = Column(Integer, default=0)
    status = Column(String(20), default='under_approval')
    role_id = Column(Integer, ForeignKey('role_sprav.role_id'))
    skills_id = Column(Integer, ForeignKey('skills_sprav.skills_id'))
    role = relationship(RoleSprav)
    skills = relationship(SkillsSprav)

class ProjectMembers(Base):
    __tablename__ = 'projectmembers'
    member_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    stud_id = Column(Integer, ForeignKey('students.stud_id'))
    joindate = Column(Date)
    role_id = Column(Integer, ForeignKey('role_sprav.role_id'))
    project = relationship(Projects)
    student = relationship(Students)
    role = relationship(RoleSprav)

class ProjectManagerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.projects = []
        self.engine = create_engine('postgresql://postgres:12345@localhost/hack')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Менеджер проектов')

        self.project_list_widget = QListWidget(self)
        self.project_list_widget.itemClicked.connect(self.show_project_details)

        self.add_button = QPushButton('Добавить проект', self)
        self.add_button.clicked.connect(self.add_project)

        self.edit_button = QPushButton('Редактировать проект', self)
        self.edit_button.clicked.connect(self.edit_project)

        self.approve_button = QPushButton('Утвердить проект', self)
        self.approve_button.clicked.connect(self.approve_project)

        self.refresh_button = QPushButton('Обновить список', self)
        self.refresh_button.clicked.connect(self.update_project_list)

        self.analytics_button = QPushButton('Статистика проектов', self)
        self.analytics_button.clicked.connect(self.show_project_analytics)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Список проектов:'))

        self.project_list_widget.setStyleSheet("background-color: white; border: 1px solid violet;")

        layout.addWidget(self.project_list_widget)
        layout.addWidget(self.add_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.approve_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.analytics_button)

        self.setLayout(layout)

    def eventFilter(self, source, event):
        if event.type() == event.MouseButtonPress and event.buttons() == Qt.LeftButton:
            self.starting_selection = True
            return True
        elif event.type() == event.MouseMove and event.buttons() == Qt.LeftButton and self.starting_selection:
            index = self.project_list_widget.indexAt(event.pos())
            if index.isValid():
                self.project_list_widget.setCurrentIndex(index)
            return True
        elif event.type() == event.MouseButtonRelease and event.buttons() == Qt.LeftButton and self.starting_selection:
            self.starting_selection = False
            return True
        return super().eventFilter(source, event)

    def select_all_projects(self):
        for i in range(self.project_list_widget.count()):
            item = self.project_list_widget.item(i)
            item.setSelected(True)

    def clear_project_selection(self):
        self.project_list_widget.clearSelection()

    def add_project(self):
        project_name, ok = QInputDialog.getText(self, 'Добавить проект', 'Введите название проекта:')
        if ok and project_name:
            project_description, ok = QInputDialog.getText(self, 'Добавить проект', 'Введите описание проекта:')
            if ok and project_description:
                current_date = datetime.now().date()
                project = Projects(p_name=project_name, description=project_description, status='Новый', startdate=current_date, endgate=current_date, role_id=1, skills_id=1)
                self.session.add(project)
                self.session.commit()
                self.update_project_list()

    def edit_project(self):
        selected_item = self.project_list_widget.currentItem()
        if selected_item:
            selected_project = self.projects[self.project_list_widget.row(selected_item)]

            options = ['В процессе', 'Завершен', 'Изменить название', 'Изменить описание', 'Удалить проект']
            choice, ok = QInputDialog.getItem(self, 'Редактировать проект', 'Выберите действие:', options)

            if ok:
                if choice in ['В процессе', 'Завершен']:
                    selected_project.status = choice
                elif choice == 'Изменить название':
                    new_name, ok = QInputDialog.getText(self, 'Редактировать проект', 'Введите новое название проекта:', text=selected_project.p_name)
                    if ok:
                        selected_project.p_name = new_name
                elif choice == 'Изменить описание':
                    new_description, ok = QInputDialog.getText(self, 'Редактировать проект', 'Введите новое описание проекта:', text=selected_project.description)
                    if ok:
                        selected_project.description = new_description
                elif choice == 'Удалить проект':
                    confirm = QMessageBox.question(self, 'Удалить проект', 'Вы уверены, что хотите удалить проект?', QMessageBox.Yes | QMessageBox.No)
                    if confirm == QMessageBox.Yes:
                        self.session.delete(selected_project)

                self.session.commit()
                self.update_project_list()

    def approve_project(self):
        selected_item = self.project_list_widget.currentItem()
        if selected_item:
            selected_project = self.projects[self.project_list_widget.row(selected_item)]
            selected_project.published = 1
            self.session.commit()
            self.update_project_list()

    def show_project_analytics(self):
        total_projects = self.session.query(Projects).count()
        approved_projects = self.session.query(Projects).filter_by(published=1).count()
        in_progress_projects = self.session.query(Projects).filter_by(status='В процессе').count()

        analytics_text = f"Всего проектов: {total_projects}\nУтвержденных проектов: {approved_projects}\nПроектов в процессе: {in_progress_projects}"
        QMessageBox.information(self, 'Статистика проектов', analytics_text)

    def show_project_details(self, item):
        selected_project = self.projects[self.project_list_widget.row(item)]
        details = f"Название: {selected_project.p_name}\nОписание: {selected_project.description}\nСтатус: {selected_project.status}"
        QMessageBox.information(self, 'Детали проекта', details)

    def update_project_list(self):
        self.project_list_widget.clear()
        self.projects = self.session.query(Projects).order_by(Projects.project_id.desc()).all()
        for project in self.projects:
            self.project_list_widget.addItem(project.p_name)

    def closeEvent(self, event):
        self.session.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    project_manager = ProjectManagerApp()
    project_manager.show()
    sys.exit(app.exec_())
