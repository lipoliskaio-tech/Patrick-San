"""
Cliente Desktop - Interface gráfica principal (Tkinter).

Fluxo:
1. Verifica manutenção antes de exibir a tela de login.
2. Login apenas com a chave de licença (com opção "Lembrar licença").
3. Após login, mostra tela principal com dias restantes, status, versão
   e envia heartbeats periódicos em background.
4. Verifica atualização automática ao iniciar.
"""
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from license_client import LicenseClient, CURRENT_VERSION
from local_storage import load_license, save_license

HEARTBEAT_INTERVAL_SECONDS = 45


class LicenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meu Software")
        self.geometry("420x360")
        self.resizable(False, False)

        self.client = LicenseClient()
        self._heartbeat_thread = None
        self._stop_heartbeat = threading.Event()

        self._build_login_screen()
        self.after(200, self._startup_checks)

    # ------------------------------------------------------------------
    # Verificações de inicialização
    # ------------------------------------------------------------------
    def _startup_checks(self):
        try:
            maintenance = self.client.check_maintenance()
        except Exception as exc:
            messagebox.showwarning(
                "Aviso", f"Não foi possível conectar ao servidor.\n\nDetalhes: {exc}"
            )
            return

        if maintenance.get("is_active"):
            messagebox.showinfo(
                "Manutenção",
                maintenance.get("message") or "Sistema em manutenção. Tente novamente mais tarde.",
            )
            self.destroy()
            return

        try:
            update_info = self.client.check_update()
            if update_info.get("update_available"):
                self._prompt_update(update_info)
        except Exception:
            # Falha ao checar atualização não deve impedir o uso do programa.
            pass

        remembered_key = load_license()
        if remembered_key:
            self.license_entry.insert(0, remembered_key)
            self.remember_var.set(True)

    def _prompt_update(self, update_info: dict):
        is_mandatory = update_info.get("is_mandatory", False)
        message = (
            f"Uma nova versão ({update_info['latest_version']}) está disponível.\n\n"
            f"{update_info.get('changelog') or ''}\n\n"
            f"Baixar agora?"
        )
        if is_mandatory:
            messagebox.showwarning(
                "Atualização obrigatória",
                f"{message}\n\nEsta atualização é obrigatória para continuar usando o programa.",
            )
            import webbrowser

            webbrowser.open(update_info["download_url"])
            self.destroy()
        else:
            if messagebox.askyesno("Atualização disponível", message):
                import webbrowser

                webbrowser.open(update_info["download_url"])

    # ------------------------------------------------------------------
    # Tela de login
    # ------------------------------------------------------------------
    def _build_login_screen(self):
        self.login_frame = ttk.Frame(self, padding=24)
        self.login_frame.pack(fill="both", expand=True)

        ttk.Label(self.login_frame, text="Ativação de Licença", font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))

        ttk.Label(self.login_frame, text="Chave de licença:").pack(anchor="w")
        self.license_entry = ttk.Entry(self.login_frame, width=40)
        self.license_entry.pack(pady=(4, 12))

        self.remember_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.login_frame, text="Lembrar licença", variable=self.remember_var
        ).pack(anchor="w", pady=(0, 12))

        self.login_button = ttk.Button(self.login_frame, text="Entrar", command=self._on_login)
        self.login_button.pack(fill="x", pady=(4, 0))

        self.status_label = ttk.Label(self.login_frame, text="", foreground="red", wraplength=360)
        self.status_label.pack(pady=(12, 0))

    def _on_login(self):
        license_key = self.license_entry.get().strip()
        if not license_key:
            self.status_label.config(text="Informe a chave de licença.")
            return

        self.login_button.config(state="disabled", text="Verificando...")
        self.status_label.config(text="")
        threading.Thread(target=self._do_login, args=(license_key,), daemon=True).start()

    def _do_login(self, license_key: str):
        try:
            result = self.client.login(license_key)
        except Exception as exc:
            self.after(0, self._on_login_error, f"Falha na comunicação com o servidor.\n{exc}")
            return

        if not result.get("success"):
            self.after(0, self._on_login_error, result.get("message", "Falha no login."))
            return

        save_license(license_key, self.remember_var.get())
        self.after(0, self._show_main_screen, result)

    def _on_login_error(self, message: str):
        self.login_button.config(state="normal", text="Entrar")
        self.status_label.config(text=message)

    # ------------------------------------------------------------------
    # Tela principal (pós-login)
    # ------------------------------------------------------------------
    def _show_main_screen(self, login_result: dict):
        self.login_frame.destroy()

        main_frame = ttk.Frame(self, padding=24)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Licença ativada com sucesso!", font=("Segoe UI", 14, "bold"), foreground="#16a34a").pack(pady=(0, 16))

        info = ttk.Frame(main_frame)
        info.pack(fill="x")

        def row(label, value):
            line = ttk.Frame(info)
            line.pack(fill="x", pady=3)
            ttk.Label(line, text=label, width=18).pack(side="left")
            ttk.Label(line, text=value, font=("Segoe UI", 10, "bold")).pack(side="left")

        if login_result.get("is_lifetime"):
            row("Dias restantes:", "Vitalícia")
            row("Data de expiração:", "Nunca expira")
        else:
            row("Dias restantes:", str(login_result.get("days_remaining", "-")))
            expires_at = login_result.get("expires_at") or "-"
            row("Data de expiração:", str(expires_at))

        row("Status da licença:", login_result.get("status", "-"))
        row("Versão atual:", CURRENT_VERSION)
        if login_result.get("customer_name"):
            row("Cliente:", login_result["customer_name"])

        ttk.Separator(main_frame).pack(fill="x", pady=16)

        ttk.Button(main_frame, text="Iniciar Programa", command=self._launch_program).pack(fill="x")
        ttk.Button(main_frame, text="Sair", command=self._on_close).pack(fill="x", pady=(8, 0))

        self._start_heartbeat()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _launch_program(self):
        messagebox.showinfo(
            "Iniciar", "Aqui você deve chamar a lógica real do seu programa principal."
        )

    # ------------------------------------------------------------------
    # Heartbeat em background
    # ------------------------------------------------------------------
    def _start_heartbeat(self):
        self._stop_heartbeat.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        while not self._stop_heartbeat.is_set():
            self.client.send_heartbeat()
            self._stop_heartbeat.wait(HEARTBEAT_INTERVAL_SECONDS)

    def _on_close(self):
        self._stop_heartbeat.set()
        self.destroy()


if __name__ == "__main__":
    app = LicenseApp()
    app.mainloop()
