import subprocess

def run_script(command):
    print(f"🔄 Eseguo: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"❌ Errore durante l'esecuzione di: {command}")
        exit(1)  # esce se c'è errore
    else:
        print(f"✅ Comando completato: {command}")

def run_all():
    run_script("python3 fetch_championships.py")
    run_script("python3 clean_tournament_decks.py")
    run_script("python3 import_to_sqlite.py")
    print("🎉 Tutto completato!")

if __name__ == "__main__":
    run_all()
