from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
GIGACHAT_API_KEY = "api_key"


class Agent:
    def __init__(self, role_prompt: str):
        self.payload = Chat(
            messages=[
                Messages(
                    role=MessagesRole.SYSTEM,
                    content=role_prompt,
                )
            ],
            temperature=0.3,
        )

    def query(self, prompt: str):
        with GigaChat(credentials=GIGACHAT_API_KEY, verify_ssl_certs=False) as giga:
            self.payload.messages.append(
                Messages(
                    role=MessagesRole.USER,
                    content=prompt,
                )
            )

            response = giga.chat(self.payload)
            self.payload.messages.append(response.choices[0].message)
            return response.choices[0].message.content


class Environment:
    def __init__(self,
                 primary_role: str,
                 secondary_role_1: str,
                 secondary_role_2: str
                 ):
        self.primary_agent = Agent(primary_role)
        self.secondary_agent_1 = Agent(secondary_role_1)
        self.secondary_agent_2 = Agent(secondary_role_2)

    def dialog_episode(self, secondary_prompt_1: str, secondary_prompt_2: str, test=False):
        response_agent_1 = self.secondary_agent_1.query(secondary_prompt_1)
        response_agent_2 = self.secondary_agent_2.query(secondary_prompt_2)

        response_primary_raw = self.primary_agent.query(f'прокурор: "{response_agent_1}"')
        response_primary_final = self.primary_agent.query(f'адвокат: "{response_agent_2}"')

        if test:
            print(
                f" прокурор: {response_agent_1}\n судья: {response_primary_raw}\n адвокат: {response_agent_2}\n судья: {response_primary_final}")

        return response_primary_raw, response_primary_final, response_agent_1, response_agent_2

    def get_order(self):
        response_primary_final = self.primary_agent.query("Комада: вынести решение")

        return response_primary_final


import tkinter as tk
from tkinter import ttk, scrolledtext


class ChatInterface:
    def __init__(self, master):
        self.master = master
        master.title("Диалоговый интерфейс")

        # Хранилища для промптов
        self.secondary_prompt_1 = ""  # Для прокурора
        self.secondary_prompt_2 = ""  # Для адвоката

        # Основной текстовый виджет
        self.history_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, state='disabled')
        self.history_area.pack(padx=10, pady=7, fill=tk.BOTH, expand=True)

        # Панель управления
        control_frame = ttk.Frame(master)
        control_frame.pack(pady=5, fill=tk.X)

        # Кнопки действий
        self.court_btn = ttk.Button(control_frame, text="Решение Суда", command=self.show_court_order)
        self.court_btn.pack(side=tk.LEFT, padx=2)

        self.get_btn = ttk.Button(control_frame, text="Получить", command=self.get_responses)
        self.get_btn.pack(side=tk.LEFT, padx=2)

        self.send_btn = ttk.Button(control_frame, text="Отправить", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=2)

        # Переключатель режима
        self.mode_var = tk.StringVar(value="prosecutor")
        mode_switch = ttk.Frame(master)
        mode_switch.pack(pady=5)

        ttk.Radiobutton(mode_switch, text="Прокурор", variable=self.mode_var,
                        value="prosecutor", command=self.update_prompts).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_switch, text="Адвокат", variable=self.mode_var,
                        value="lawyer", command=self.update_prompts).pack(side=tk.LEFT, padx=5)

        # Поле ввода
        self.input_field = ttk.Entry(master)
        self.input_field.pack(padx=20, pady=10, fill=tk.X)
        self.input_field.bind("<Return>", lambda e: self.send_message())

        # Инициализируем начальное значение поля ввода
        self.update_prompts()

    def update_prompts(self):
        """Обновление поля ввода в соответствии с выбранным режимом"""
        current_mode = self.mode_var.get()
        if current_mode == "prosecutor":
            self.input_field.delete(0, tk.END)
            self.input_field.insert(0, self.secondary_prompt_1)
        else:
            self.input_field.delete(0, tk.END)
            self.input_field.insert(0, self.secondary_prompt_2)

    def update_history(self, text):
        """Обновление истории"""
        self.history_area.configure(state='normal')
        self.history_area.insert(tk.END, text + "\n\n")
        self.history_area.configure(state='disabled')
        self.history_area.see(tk.END)

    def send_message(self):
        """Отправка сообщения"""
        message = self.input_field.get()
        if message:
            # Сохраняем в соответствующий промпт
            if self.mode_var.get() == "prosecutor":
                self.secondary_prompt_1 = message
            else:
                self.secondary_prompt_2 = message

            self.update_history(f"Пользователь ({self.mode_var.get()}): {message}")
            self.input_field.delete(0, tk.END)

    def get_responses(self):
        """Получение ответов системы"""
        # Сохраняем текущее сообщение перед получением ответа
        current_message = self.input_field.get()
        if current_message:
            self.send_message()  # Сохраняем сообщение в соответствующий промпт

        # Вызываем диалог с сохраненными промптами
        r_raw, r_final, r_agent1, r_agent2 = court.dialog_episode(
            secondary_prompt_1=self.secondary_prompt_1,
            secondary_prompt_2=self.secondary_prompt_2
        )

        response = (f"Прокурор: {r_agent1}\nАдвокат: {r_agent2}\n"
                    f"Система:\nRAW: {r_raw}\nFinal: {r_final}\n"
                    )

        self.update_history(response)

    def show_court_order(self):
        """Показать решение суда"""
        order = court.get_order()
        self.update_history(f"Суд принял решение: {order}")


primary_role = 'Ты судья гражданского суда в России и ведешь судебный процесс. Ты по очереди выслушиваешь стороны обвинителя (прокурора) и защиты (адвоката). Например: прокурор: "Уважаемый суд! Сегодня я, как представитель прокуратуры, выступаю в защиту законных интересов гражданина РФ Ивана Иванова". После того, как обе стороны высказались ты при необходимости можешь задать им вопросы. Тебе необходимо вынести решение суда после кодовой фразы "Комада: вынести решение"'
secondary_role_1 = "Ты прокурор гражданского суда в России. Ты выслушиваешь описание материала дела и выступаешь по нему перед судом, отвечая на вопросы судьи если тебе их зададут"
secondary_role_2 = "Ты адвокат гражданского суда в России. Ты выслушиваешь описание материала дела и выступаешь по нему перед судом, отвечая на вопросы судьи если тебе их зададут"

court = Environment(primary_role, secondary_role_1, secondary_role_2)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatInterface(root)
    root.geometry("1000x600")
    root.mainloop()