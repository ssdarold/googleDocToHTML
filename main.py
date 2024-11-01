import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Путь к вашим учетным данным
CREDENTIALS_FILE = 'credentials.json'

# ID вашего Google Doc документа
DOCUMENT_ID = '1rhUTTiiniO9AanYRyTrfI59M4Q_FNVcSU6xWpvRplQE'

# Получение авторизации через OAuth
def get_document():
    # Области доступа, необходимые для работы с Google Docs
    SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

    # Проверяем наличие токена
    creds = None
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    except Exception as e:
        print(f"Error reading token: {e}")
        creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Передаем Request объект
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('docs', 'v1', credentials=creds)
    document = service.documents().get(documentId=DOCUMENT_ID).execute()
    return document

# Преобразование форматирования текста (жирный, курсив)
def format_text_style(text_element):
    text_content = text_element.get('content', '')
    text_style = text_element.get('textStyle', {})

    if text_style.get('bold'):
        text_content = f"<strong>{text_content}</strong>"
    if text_style.get('italic'):
        text_content = f"<em>{text_content}</em>"
    if text_style.get('underline'):
        text_content = f"<u>{text_content}</u>"
    if text_style.get('strikethrough'):
        text_content = f"<s>{text_content}</s>"

    return text_content

# Генерация HTML с учетом правил
def generate_html(document):
    html_content = ""
    toc_content = "<div class='toc_block'>\n<ul>\n"
    id_counter = 1
    in_list = False
    list_type = None

    for element in document.get("body").get("content"):
        if 'paragraph' in element:
            paragraph = element['paragraph']
            if paragraph.get('paragraphStyle', {}).get('namedStyleType') in ['HEADING_1', 'HEADING_2', 'HEADING_3']:
                if in_list:
                    html_content += f"</{list_type}>\n"
                    in_list = False
                heading_type = paragraph['paragraphStyle']['namedStyleType']
                text = ''.join([format_text_style(elem['textRun']) for elem in paragraph['elements'] if 'textRun' in elem])
                html_id = f"heading-{id_counter}"
                toc_content += f"<li><a href='#{html_id}'>{text.strip()}</a></li>\n"
                if heading_type == 'HEADING_1':
                    html_content += f"<h1 id='{html_id}' class='h1_article'>{text.strip()}</h1>\n"
                elif heading_type == 'HEADING_2':
                    html_content += f"<h2 id='{html_id}' class='h2_article'>{text.strip()}</h2>\n"
                elif heading_type == 'HEADING_3':
                    html_content += f"<h3 id='{html_id}' class='h3_article'>{text.strip()}</h3>\n"
                id_counter += 1
            elif paragraph.get('bullet'):
                if not in_list:
                    list_type = 'ul' if paragraph['bullet'].get('listId') else 'ol'
                    html_content += f"<{list_type}>\n"
                    in_list = True
                list_item_text = ''.join([format_text_style(elem['textRun']) for elem in paragraph['elements'] if 'textRun' in elem])
                html_content += f"<li>{list_item_text.strip()}</li>\n"
            else:
                if in_list:
                    html_content += f"</{list_type}>\n"
                    in_list = False
                text = ''.join([format_text_style(elem['textRun']) for elem in paragraph['elements'] if 'textRun' in elem])
                html_content += f"<p class='p_article'>{text.strip()}</p>\n"

    if in_list:
        html_content += f"</{list_type}>\n"
    toc_content += "</ul>\n</div>\n"

    return toc_content + html_content

# Основная логика
def main():
    document = get_document()
    html_result = generate_html(document)
    with open("article.html", "w", encoding="utf-8") as file:
        file.write(html_result)

if __name__ == '__main__':
    main()
