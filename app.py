#!/usr/bin/env python3
# PrivateMC Server: installer + Website/Admin-Panel in one file.
import os, sys, re, platform, subprocess, threading, urllib.request, json, tarfile, zipfile, shutil, time, hmac, secrets, hashlib, socket, struct, io, atexit, signal, webbrowser, getpass, base64, tempfile
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, jsonify, request, session, redirect, render_template, send_file, abort
from werkzeug.security import generate_password_hash, check_password_hash
import psutil

WEB_PORT = int(os.environ.get("PORT", "5000"))

# --- KORRIGIERTER SICHERER IMPORT GANZ OBEN IN APP.PY ---
try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    # Falls pystray beim Importieren abstürzt (wie auf Headless-Linux), 
    # tun wir so, als wäre es gar nicht installiert.
    pystray = None
    Image = None
    ImageDraw = None


BASE_DIR = Path(os.path.expanduser("~/PrivateMC")).resolve()
SERVER_DIR = BASE_DIR / "server"
JAR_PATH = SERVER_DIR / "server.jar"
EULA_PATH = SERVER_DIR / "eula.txt"
JAVA_DIR = BASE_DIR / "bin-java"
BACKUP_DIR = BASE_DIR / "backups"
CONFIG_PATH = BASE_DIR / "web-config.json"
JAVA_VERSION = 25
PAPER_API = "https://fill.papermc.io/v3/projects/paper"
USER_AGENT = "PrivateMC/1.0"
for d in (SERVER_DIR, JAVA_DIR, BACKUP_DIR): d.mkdir(parents=True, exist_ok=True)

# PyInstaller speichert gebündelte Ressourcen temporär in sys._MEIPASS.
if getattr(sys, "frozen", False):
    CURRENT_DIR = Path(sys._MEIPASS)
else:
    CURRENT_DIR = Path(__file__).resolve().parent


# --- Standard-Server-Icon (direkt in app.py eingebettet) ---
# Wird nur beim ersten Start angelegt; ein eigenes Server-Icon bleibt erhalten.
DEFAULT_SERVER_ICON_B64 = (
    "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"
)
SERVER_ICON_PATH = SERVER_DIR / "server-icon.png"

def ensure_default_server_icon():
    try:
        if not SERVER_ICON_PATH.exists():
            SERVER_ICON_PATH.write_bytes(base64.b64decode(DEFAULT_SERVER_ICON_B64))
    except Exception as exc:
        print(f"PrivateMC: Standard-Server-Icon konnte nicht angelegt werden: {exc}")

ensure_default_server_icon()

app = Flask(
    __name__,
    template_folder=str(CURRENT_DIR / "templates"),
    static_folder=str(CURRENT_DIR / "static")
)
app.config.update(SESSION_COOKIE_SAMESITE="Strict", SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
                  PERMANENT_SESSION_LIFETIME=8*3600, MAX_CONTENT_LENGTH=200*1024*1024,
                  SEND_FILE_MAX_AGE_DEFAULT=0)
mc_process = None
output_logs = []
java_executable = "java"
log_lock = threading.Lock()
task_lock = threading.Lock()
task = {"name": None, "err": None}
hist = {"cpu": [], "ram": []}
last_cpu = None
started_at = None
ram_gb = 2
try:
    ram_gb = max(1, int(json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get("ram_gb", 2)))
except Exception:
    pass
fails = {}
cache = {"t": 0, "v": None}

def load_config():
    global ADMIN_USER, ADMIN_PASSWORD_HASH
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}

    if not cfg.get("secret_key"):
        cfg["secret_key"] = secrets.token_hex(32)

    ADMIN_USER = os.environ.get("MC_ADMIN_USER", "admin")
    env_password = os.environ.get("MC_ADMIN_PASSWORD")

    # Ein Passwort aus der Umgebungsvariable hat Vorrang. Es wird ebenfalls
    # nur als Hash gespeichert.
    if env_password:
        ADMIN_PASSWORD_HASH = generate_password_hash(env_password)
        cfg["admin_password_hash"] = ADMIN_PASSWORD_HASH
        cfg.pop("admin_password", None)
    elif cfg.get("admin_password_hash"):
        ADMIN_PASSWORD_HASH = cfg["admin_password_hash"]
    else:
        # Beim ersten Start das Admin-Passwort in einem Dialog abfragen,
        # da die Windows-Version ohne Konsole läuft.
        has_gui = (
            os.name == "nt"
            or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        )
        if has_gui and (getattr(sys, "frozen", False) or sys.stdin is None):
            try:
                import tkinter as tk
                from tkinter import simpledialog, messagebox
                root = tk.Tk()
                root.withdraw()
                password = None
                while True:
                    first = simpledialog.askstring(
                        "PrivateMC einrichten",
                        f"Lege ein Passwort für das Admin-Panel fest.\nBenutzername: {ADMIN_USER}",
                        show="*", parent=root
                    )
                    if first is None:
                        root.destroy()
                        raise SystemExit(0)
                    if not first:
                        messagebox.showwarning("PrivateMC", "Das Passwort darf nicht leer sein.", parent=root)
                        continue
                    second = simpledialog.askstring(
                        "Passwort bestätigen", "Gib das Passwort erneut ein:",
                        show="*", parent=root
                    )
                    if second is None:
                        root.destroy()
                        raise SystemExit(0)
                    if not hmac.compare_digest(first, second):
                        messagebox.showerror("PrivateMC", "Die Passwörter stimmen nicht überein.", parent=root)
                        continue
                    password = first
                    break
                root.destroy()
                ADMIN_PASSWORD_HASH = generate_password_hash(password)
                messagebox.showinfo(
                    "PrivateMC", "Admin-Passwort wurde gespeichert.\n\n"
                    f"Benutzername: {ADMIN_USER}\nDas Passwort wurde nicht im Klartext gespeichert."
                )
            except SystemExit:
                raise
            except Exception as exc:
                raise RuntimeError(f"Admin-Passwortdialog konnte nicht geöffnet werden: {exc}") from exc
        else:
            print("\nPrivateMC – ADMIN-EINRICHTUNG")
            print("Benutzername für die Serververwaltung: " + ADMIN_USER)
            while True:
                password = getpass.getpass("\nSetzen Sie Ihr Passwort für die Serververwaltung: ")
                if not password:
                    print("Das Passwort darf nicht leer sein. Bitte erneut versuchen.")
                    continue
                repeated = getpass.getpass("Bitte wiederholen Sie Ihr Passwort: ")
                if not hmac.compare_digest(password, repeated):
                    print("Die Passwörter stimmen nicht überein. Bitte versuchen Sie es erneut.\n")
                    continue
                ADMIN_PASSWORD_HASH = generate_password_hash(password)
                break
        cfg["admin_password_hash"] = ADMIN_PASSWORD_HASH
        cfg.pop("admin_password", None)

    cfg["admin_user"] = ADMIN_USER
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        CONFIG_PATH.chmod(0o600)
    except OSError:
        pass
    app.secret_key = cfg["secret_key"]

load_config()

def download_file(url, destination, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept":"application/octet-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as response, open(destination, "wb") as out:
        shutil.copyfileobj(response, out)

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def get_java_major(executable):
    try:
        r = subprocess.run([str(executable), "-version"], capture_output=True, text=True, timeout=10)
        m = re.search(r'version "([^"]+)"', r.stdout+r.stderr)
        if not m: return None
        v=m.group(1)
        return int(v.split(".")[1] if v.startswith("1.") else v.split(".")[0])
    except Exception: return None

def find_portable_java():
    expected = "java.exe" if os.name == "nt" else "java"
    for root, dirs, files in os.walk(JAVA_DIR):
        if expected in files and Path(root).name == "bin":
            candidate=Path(root)/expected
            if get_java_major(candidate)==JAVA_VERSION: return str(candidate)
    return None

def install_portable_java():
    system=platform.system().lower(); machine=platform.machine().lower()
    arch={"x86_64":"x64","amd64":"x64","aarch64":"aarch64","arm64":"aarch64"}.get(machine)
    if not arch: raise RuntimeError("Nicht unterstützte CPU-Architektur: "+machine)
    os_name={"windows":"windows","linux":"linux","darwin":"mac"}.get(system)
    if not os_name: raise RuntimeError("Nicht unterstütztes Betriebssystem: "+system)
    archive_path=JAVA_DIR/("java.zip" if system=="windows" else "java.tar.gz")
    url=f"https://api.adoptium.net/v3/binary/latest/{JAVA_VERSION}/ga/{os_name}/{arch}/jdk/hotspot/normal/eclipse"
    print(f"Lade Java {JAVA_VERSION} herunter...")
    try:
        download_file(url, archive_path)
        if archive_path.suffix==".zip":
            with zipfile.ZipFile(archive_path) as z:
                root=JAVA_DIR.resolve()
                for m in z.infolist():
                    if os.path.commonpath([str(root),str((JAVA_DIR/m.filename).resolve())]) != str(root): raise RuntimeError("Unsicherer Pfad im Java-Archiv.")
                z.extractall(JAVA_DIR)
        else:
            with tarfile.open(archive_path,"r:gz") as t:
                root=JAVA_DIR.resolve()
                for m in t.getmembers():
                    if os.path.commonpath([str(root),str((JAVA_DIR/m.name).resolve())]) != str(root): raise RuntimeError("Unsicherer Pfad im Java-Archiv.")
                t.extractall(JAVA_DIR, filter="data")
        exe=find_portable_java()
        if not exe: raise RuntimeError("Java wurde entpackt, aber nicht gefunden.")
        if os.name!="nt": os.chmod(exe, os.stat(exe).st_mode|0o111)
        return exe
    finally:
        if archive_path.exists(): archive_path.unlink()

def setup_java():
    global java_executable
    sj=shutil.which("java")
    if sj and (get_java_major(sj) or 0)>=JAVA_VERSION:
        java_executable=sj; print(f"[✓] System-Java {get_java_major(sj)} gefunden."); return
    p=find_portable_java()
    if p: java_executable=p; print("[✓] Vorhandenes portables Java gefunden."); return
    java_executable=install_portable_java()

def version_key(v):
    m=re.match(r"^(\d+(?:\.\d+)*)(.*)$",v)
    if not m:return ((),0,v)
    return (tuple(int(x) for x in m.group(1).split(".")),1 if not m.group(2) else 0,m.group(2).lower())

def paper_versions():
    try:
        p=get_json(PAPER_API)
        out=[]
        for vals in p.get("versions",{}).values():
            if isinstance(vals,list): out += [x for x in vals if isinstance(x,str)]
        return sorted(set(out),key=version_key,reverse=True)
    except Exception:
        return []

def download_paper_version(version):
    api=PAPER_API
    builds=get_json(f"{api}/versions/{version}/builds")
    stable=[b for b in builds if isinstance(b,dict) and b.get("channel")=="STABLE" and b.get("downloads",{}).get("server:default",{}).get("url")]
    if not stable: raise RuntimeError(f"Kein stabiler Paper-Build für {version} gefunden.")
    b=max(stable,key=lambda x:int(x["id"])); info=b["downloads"]["server:default"]
    tmp=JAR_PATH.with_suffix(".jar.download")
    try:
        download_file(info["url"],tmp)
        if info.get("checksums",{}).get("sha256"):
            h=hashlib.sha256()
            with open(tmp,"rb") as f:
                for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
            if h.hexdigest().lower()!=info["checksums"]["sha256"].lower():raise RuntimeError("SHA-256-Prüfung fehlgeschlagen.")
        os.replace(tmp,JAR_PATH)
    finally:
        if tmp.exists():tmp.unlink()
    return b["id"]

def setup_paper():
    if JAR_PATH.exists() and JAR_PATH.stat().st_size>1024*1024:
        print("[✓] server.jar existiert bereits."); return
    versions=paper_versions()
    if not versions: raise RuntimeError("Paper-Versionen konnten nicht von PaperMC geladen werden.")
    for v in versions:
        # Stable builds only; skip versions with no stable release.
        try:
            print(f"[!] Prüfe Paper {v}...")
            build=download_paper_version(v)
            print(f"[✓] Paper {v}, Build {build} installiert."); return
        except Exception as e:
            print(f"[!] {v}: {e}")
    raise RuntimeError("Kein stabiler Paper-Build gefunden.")

def request_eula_consent():
    if EULA_PATH.exists() and re.search(r"(?im)^\s*eula\s*=\s*true\s*$", EULA_PATH.read_text(errors="replace")):
        print("[✓] Eine Zustimmung zur EULA liegt bereits vor.")
        return True

    eula_url = "https://aka.ms/MinecraftEULA"
    # In einer --windowed-PyInstaller-EXE gibt es keine Konsole für input().
    has_gui = (
        os.name == "nt"
        or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    )
    if has_gui and (getattr(sys, "frozen", False) or sys.stdin is None):
        try:
            import tkinter as tk
            from tkinter import messagebox
            webbrowser.open(eula_url)
            root = tk.Tk()
            root.withdraw()
            accepted = messagebox.askyesno(
                "Minecraft EULA",
                "Die Minecraft-EULA wurde im Browser geöffnet:\n\n"
                f"{eula_url}\n\n"
                "Hast du sie gelesen und stimmst du ihr zu?"
            )
            root.destroy()
            if not accepted:
                return False
            EULA_PATH.write_text(
                "# Accepted after explicit consent.\neula=true\n",
                encoding="utf-8"
            )
            return True
        except Exception as exc:
            print("EULA-Abfrage konnte nicht geöffnet werden:", exc)
            return False

    print("\nMinecraft EULA:", eula_url)
    while True:
        try:
            answer = input("Hast du die EULA gelesen und stimmst du zu? (ja/nein): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        if answer in ("ja", "j", "yes", "y"):
            EULA_PATH.write_text(
                "# Accepted after explicit consent.\neula=true\n",
                encoding="utf-8"
            )
            return True
        if answer in ("nein", "n", "no"):
            return False
        print("Bitte antworte mit ja oder nein.")

def read_output(process):
    global output_logs
    if process.stdout is None:return
    try:
        for line in iter(process.stdout.readline,""):
            if not line:break
            clean=line.rstrip()
            print("[MC-Server] "+clean)
            with log_lock:
                output_logs.append(clean)
                del output_logs[:-500]
    finally:
        try:process.stdout.close()
        except Exception:pass

def is_running():
    return mc_process is not None and mc_process.poll() is None

def start_server_process():
    global mc_process, started_at
    if not JAR_PATH.exists(): raise RuntimeError("server.jar wurde nicht gefunden.")
    if not EULA_PATH.exists() or not re.search(r"(?im)^\s*eula\s*=\s*true\s*$",EULA_PATH.read_text(errors="replace")):
        raise RuntimeError("EULA-Zustimmung fehlt.")
    if is_running(): raise RuntimeError("Der Server läuft bereits.")
    # Bei einer frischen Installation den PrivateMC-Standard setzen,
    # bestehende individuelle MOTDs aber unverändert lassen.
    props_path = SERVER_DIR / "server.properties"
    if props_path.exists():
        current_props = read_props()
        if current_props.get("motd", "A Minecraft Server") == "A Minecraft Server":
            write_props({"motd": "Ein PrivateMC Server"})
    else:
        write_props({"motd": "Ein PrivateMC Server"})
    args=[java_executable,f"-Xms{min(ram_gb,1)}G",f"-Xmx{ram_gb}G","-jar",str(JAR_PATH),"nogui"]
    mc_process=subprocess.Popen(args,cwd=SERVER_DIR,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    started_at=datetime.now(timezone.utc).isoformat()
    threading.Thread(target=read_output,args=(mc_process,),daemon=True).start()

def send_command(cmd):
    if not is_running(): return "Der Server läuft nicht."
    cmd=cmd.strip().lstrip("/")
    if not cmd or len(cmd)>1000 or "\n" in cmd or "\r" in cmd: return "Ungültiger Befehl."
    try:
        mc_process.stdin.write(cmd+"\n"); mc_process.stdin.flush()
        return "Befehl gesendet: "+cmd
    except Exception as e:return "Befehl konnte nicht gesendet werden: "+str(e)

def run_bg(label, fn):
    with task_lock:
        if task["name"]: return jsonify(error=f"Bitte warten: „{task['name']}“ läuft noch."),409
        task.update(name=label,err=None)
    def worker():
        try: fn()
        except Exception as e: task["err"]=f"{label} fehlgeschlagen: {e}"
        finally: task["name"]=None; cache["t"]=0
    threading.Thread(target=worker,daemon=True).start()
    return jsonify(ok=True,message=label+" …")

def admin(f):
    @wraps(f)
    def wrapper(*a,**kw):
        if not session.get("ok"):
            return (jsonify(error="login"),401) if request.path.startswith("/api") else redirect("/login")
        if request.method=="POST" and request.headers.get("X-Req")!="1": abort(400)
        return f(*a,**kw)
    return wrapper

NAME=re.compile(r"^[.A-Za-z0-9_]{1,16}$")
BKNAME=re.compile(r"^welt-[A-Za-z0-9._-]+-[\d-]+\.tar\.gz$")
PLNAME=re.compile(r"^[A-Za-z0-9._+-]{1,100}\.jar$")
SET={
"motd":("str",100,"Ein PrivateMC Server"),"gamemode":("enum",("survival","creative","adventure","spectator"),"survival"),
"difficulty":("enum",("peaceful","easy","normal","hard"),"easy"),"max-players":("int",(1,500),"20"),
"view-distance":("int",(3,32),"10"),"simulation-distance":("int",(3,32),"10"),
"pvp":("bool",None,"true"),"white-list":("bool",None,"false"),"online-mode":("bool",None,"true"),
"allow-flight":("bool",None,"false"),"enable-command-block":("bool",None,"false"),"allow-nether":("bool",None,"true"),
"spawn-monsters":("bool",None,"true"),"spawn-animals":("bool",None,"true")}
CORES=os.cpu_count() or 1

def read_props():
    p=SERVER_DIR/"server.properties"; d={}
    if p.exists():
        for line in p.read_text(encoding="utf-8",errors="replace").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1);d[k.strip()]=v.strip()
    return d
def write_props(upd):
    p=SERVER_DIR/"server.properties"; lines=p.read_text(encoding="utf-8",errors="replace").splitlines() if p.exists() else []
    seen=set();out=[]
    for line in lines:
        k=line.split("=",1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else None
        if k in upd:out.append(f"{k}={upd[k]}");seen.add(k)
        else:out.append(line)
    out += [f"{k}={v}" for k,v in upd.items() if k not in seen]
    p.write_text("\n".join(out)+"\n",encoding="utf-8")
def clean(k,v):
    typ,lim,_=SET[k]
    if typ=="bool":return "true" if v in (True,"true") else "false"
    if typ=="int":
        n=int(v)
        if not lim[0]<=n<=lim[1]:raise ValueError(f"{k}: erlaubt sind {lim[0]} bis {lim[1]}.")
        return str(n)
    if typ=="enum":
        if v not in lim:raise ValueError(f"{k}: ungültiger Wert.")
        return v
    v=str(v).replace("\n"," ").replace("\\","").strip()
    if len(v)>lim:raise ValueError(f"{k}: maximal {lim} Zeichen.")
    return v
def world_names():
    lvl=read_props().get("level-name","world")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_ .-]{0,63}",lvl):lvl="world"
    return [lvl,lvl+"_nether",lvl+"_the_end"]
def jlist(filename):
    try:return sorted((x["name"] for x in json.loads((SERVER_DIR/filename).read_text()) if x.get("name")),key=str.lower)
    except Exception:return []
def paper_plugin(path):
    try:
        with zipfile.ZipFile(path) as z:return bool({"plugin.yml","paper-plugin.yml"}&set(z.namelist()))
    except Exception:return False
def server_version():
    try:
        text="\n".join(output_logs[-200:])
        m=re.search(r"Starting minecraft server version (\d+\.\d+(?:\.\d+)?)",text)
        if m:return m.group(1)
    except Exception:pass
    m=re.search(r"(\d+\.\d+(?:\.\d+)?)",JAR_PATH.name)
    props=read_props()
    if (SERVER_DIR/"version_history.json").exists():
        try:
            m=re.search(r"MC: (\d+\.\d+(?:\.\d+)?)",(SERVER_DIR/"version_history.json").read_text())
            if m:return m.group(1)
        except Exception:pass
    # The jar filename is generic; parse startup logs if possible.
    try:
        if is_running():
            s=socket_status()
            if s and s.get("version"):return s["version"]
    except Exception:pass
    return "unbekannt"


def socket_status():
    """Liest den Status des lokalen Minecraft-Java-Servers aus."""
    import socket
    import struct
    import json
    import time

    props = read_props()
    host = props.get("server-ip", "").strip() or "127.0.0.1"

    try:
        port = int(props.get("server-port", "25565"))
    except (TypeError, ValueError):
        port = 25565

    def varint(n):
        n &= 0xffffffff
        out = bytearray()

        while True:
            b = n & 0x7f
            n >>= 7

            if n:
                b |= 0x80

            out.append(b)

            if not n:
                return bytes(out)

    def read_varint(sock):
        result = 0

        for shift in range(0, 35, 7):
            b = sock.recv(1)

            if not b:
                raise ConnectionError("Minecraft hat die Verbindung geschlossen")

            result |= (b[0] & 0x7f) << shift

            if not b[0] & 0x80:
                return result

        raise ValueError("Ungültiger Minecraft-VarInt")

    def read_exact(sock, size):
        data = bytearray()

        while len(data) < size:
            part = sock.recv(size - len(data))

            if not part:
                raise ConnectionError("Minecraft-Antwort unvollständig")

            data.extend(part)

        return bytes(data)

    def packet_varint(packet, offset):
        result = 0

        for shift in range(0, 35, 7):
            if offset >= len(packet):
                raise ValueError("Minecraft-Statuspaket unvollständig")

            b = packet[offset]
            offset += 1
            result |= (b & 0x7f) << shift

            if not b & 0x80:
                return result, offset

        raise ValueError("Ungültiger VarInt im Statuspaket")

    def text_of(value):
        if isinstance(value, str):
            return value

        if isinstance(value, list):
            return "".join(text_of(item) for item in value)

        if isinstance(value, dict):
            result = value.get("text", "")
            result += "".join(
                text_of(item) for item in value.get("extra", [])
            )
            return result

        return ""

    try:
        started = time.perf_counter()

        with socket.create_connection((host, port), timeout=3) as sock:
            sock.settimeout(3)

            address = host.encode("utf-8")

            # Handshake mit Protokollversion -1, wie im erfolgreichen Test.
            handshake = (
                varint(0)
                + varint(0xffffffff)
                + varint(len(address))
                + address
                + struct.pack(">H", port)
                + varint(1)
            )

            sock.sendall(varint(len(handshake)) + handshake)

            # Status-Request: Paketlänge 1, Paket-ID 0.
            sock.sendall(b"\x01\x00")

            packet_length = read_varint(sock)

            if not 1 <= packet_length <= 1_000_000:
                raise ValueError("Ungültige Minecraft-Paketgröße")

            packet = read_exact(sock, packet_length)

        elapsed = round((time.perf_counter() - started) * 1000)

        packet_id, offset = packet_varint(packet, 0)

        if packet_id != 0:
            raise ValueError("Unerwartete Minecraft-Statusantwort")

        json_length, offset = packet_varint(packet, offset)

        if json_length < 1 or offset + json_length > len(packet):
            raise ValueError("Ungültige JSON-Länge")

        data = json.loads(
            packet[offset:offset + json_length].decode("utf-8")
        )

        version = data.get("version") or {}
        players = data.get("players") or {}
        sample = players.get("sample") or []

        return {
            "online": True,
            "motd": text_of(data.get("description")) or "Minecraft Server",
            "version": version.get("name", "Unbekannt"),
            "ping": elapsed,
            "players": players.get("online", 0),
            "max": players.get("max", 20),
            "names": [
                player.get("name", "")
                for player in sample
                if isinstance(player, dict) and player.get("name")
            ],
        }

    except Exception as exc:
        print(f"[Minecraft-Status] {host}:{port} – {exc}")
        return None


def proc_memory():
    """RSS des Minecraft-Java-Prozesses in Bytes, plattformunabhängig."""
    if not is_running():
        return None
    try:
        return psutil.Process(mc_process.pid).memory_info().rss
    except (psutil.Error, OSError, AttributeError):
        return None


def total_memory():
    """Gesamter physischer Arbeitsspeicher des Rechners in Bytes."""
    try:
        return psutil.virtual_memory().total
    except (psutil.Error, OSError):
        return 4 * 1024**3



def sample_resources():
    """Sammelt CPU- und RAM-Auslastung des Minecraft-Prozesses."""
    global last_cpu

    while True:
        try:
            if is_running():
                proc = psutil.Process(mc_process.pid)

                # Eine echte Messung über 1 Sekunde durchführen.
                raw_cpu = proc.cpu_percent(interval=1)

                # Auf die Gesamtauslastung des Rechners normalisieren.
                cpu = max(0.0, min(100.0, raw_cpu / max(1, CORES)))

                mem = proc.memory_info().rss

                hist["cpu"] = (
                    hist["cpu"] + [round(cpu, 1)]
                )[-60:]

                hist["ram"] = (
                    hist["ram"]
                    + [round(min(100, mem / (ram_gb * 1024**3) * 100), 1)]
                )[-60:]

            else:
                last_cpu = None
                hist["cpu"] = []
                hist["ram"] = []

        except (psutil.Error, OSError, AttributeError):
            last_cpu = None

        except Exception as exc:
            print(f"[Monitoring] Fehler: {exc}")
            last_cpu = None

        time.sleep(1)


threading.Thread(
    target=sample_resources,
    daemon=True,
    name="resource-monitor"
).start()


def status():
    running = is_running()

    out = {
        "state": "running" if running else "exited",
        "since": started_at,
        "online": False,
        "players": 0,
        "max": 20,
        "version": server_version(),
        "ping": None,
        "names": []
    }

    if not running:
        return out

    result = socket_status()

    if result:
        out.update(result)

    return out

def do_backup():
    if is_running():send_command("save-all flush");time.sleep(1)
    ver=server_version().replace("/","_")
    name=f"welt-{ver}-{datetime.now():%Y%m%d-%H%M%S}.tar.gz"
    with tarfile.open(BACKUP_DIR/name,"w:gz") as t:
        for w in world_names():
            if (SERVER_DIR/w).exists():t.add(SERVER_DIR/w,arcname=w)
    return name

def run_task(label,fn):
    return run_bg(label,fn)

# Frontend: HTML-Dateien aus templates/, CSS/JS automatisch aus static/.
@app.route("/favicon.ico")
@app.route("/favicon.png")
def favicon():
    """Serves the current PrivateMC icon as the website favicon."""
    ensure_default_server_icon()
    try:
        return send_file(SERVER_ICON_PATH, mimetype="image/png", max_age=0)
    except Exception:
        return "", 404


@app.route("/")
def index():
    return render_template(
        "index.html",
        addr=os.environ.get("MC_ADDRESS") or request.host.split(":")[0]
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    err = None
    ip = request.remote_addr or "unknown"
    if request.method == "POST":
        n, t = fails.get(ip, (0, 0))
        if time.time() - t > 300:
            n = 0
        if n >= 5:
            err = "Zu viele Versuche. Bitte in 5 Minuten erneut versuchen."
        elif (
            hmac.compare_digest(request.form.get("u", ""), ADMIN_USER)
            and check_password_hash(ADMIN_PASSWORD_HASH, request.form.get("p", ""))
        ):
            session.clear()
            session["ok"] = True
            session.permanent = True
            fails.pop(ip, None)
            return redirect("/admin")
        else:
            fails[ip] = (n + 1, time.time())
            err = "Benutzername oder Passwort falsch."
    return render_template("login.html", err=err)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/admin")
@admin
def admin_page():
    return render_template(
        "admin.html",
        addr=os.environ.get("MC_ADDRESS") or request.host.split(":")[0]
    )

@app.route("/api/status")
def api_status():
    global cache
    if time.time()-cache["t"]>1:cache={"t":time.time(),"v":status()}
    out=dict(cache["v"] or {})
    mem=proc_memory();out.update(task=task["name"],cpu=(hist["cpu"][-1] if hist["cpu"] else None),
        ram=mem,ram_max=ram_gb*1024**3,cores=CORES,hc=hist["cpu"],hr=hist["ram"])
    if session.get("ok"):out["err"]=task["err"]
    return jsonify(out)

@app.route("/api/admin/power",methods=["POST"])
@admin
def power():
    a=(request.json or {}).get("action")
    if a not in ("start","stop","restart"):return jsonify(error="Ungültige Aktion."),400
    if a=="start":
        if is_running():return jsonify(error="Der Server läuft bereits.")
        return run_task("Server wird gestartet",start_server_process)
    if a=="stop":
        if not is_running():return jsonify(error="Der Server läuft nicht.")
        return run_task("Server wird gestoppt",lambda:send_command("stop"))
    def restart():
        if is_running():
            send_command("stop")
            for _ in range(90):
                if not is_running():break
                time.sleep(1)
        start_server_process()
    return run_task("Server wird neu gestartet",restart)

@app.route("/api/admin/start",methods=["POST"])
@admin
def api_start():
    if is_running(): return jsonify(error='Der Server läuft bereits.'),400
    return run_task('Server wird gestartet',start_server_process)
@app.route("/api/admin/stop",methods=["POST"])
@admin
def api_stop():
    if not is_running(): return jsonify(error='Der Server läuft nicht.'),400
    return run_task('Server wird gestoppt',lambda:send_command('stop'))

@app.route("/api/admin/console")
@admin
def console():
    with log_lock:logs="\n".join(output_logs[-500:])
    return jsonify(log=logs)
@app.route("/api/admin/cmd",methods=["POST"])
@admin
def cmd():
    c=(request.json or {}).get("cmd","").strip()
    if len(c)>1000 or "\n" in c or "\r" in c:return jsonify(error="Ungültiger Befehl.")
    return jsonify(out=send_command(c))
@app.route("/api/admin/player",methods=["POST"])
@admin
def player():
    d=request.json or {};a=d.get("action");n=d.get("name","")
    allowed={"whitelist_add":"whitelist add","whitelist_remove":"whitelist remove","op":"op","deop":"deop","kick":"kick","ban":"ban","pardon":"pardon"}
    if a not in allowed or not NAME.fullmatch(n):return jsonify(error="Bitte einen gültigen Spielernamen eingeben.")
    return jsonify(out=send_command(allowed[a]+" "+n))
@app.route("/api/admin/players")
@admin
def players():return jsonify(whitelist=jlist("whitelist.json"),ops=jlist("ops.json"),banned=jlist("banned-players.json"))

@app.route("/api/admin/settings",methods=["GET","POST"])
@admin
def settings():
    if request.method=="GET":
        p=read_props();return jsonify(values={k:p.get(k,v[2]) for k,v in SET.items()})
    vals=(request.json or {}).get("values",{})
    try:upd={k:clean(k,vals[k]) for k in SET if k in vals}
    except (ValueError,TypeError) as e:return jsonify(error=str(e) or "Ungültiger Wert.")
    write_props(upd);return jsonify(ok=True,message="Gespeichert. Änderungen gelten nach dem nächsten Neustart.")
@app.route("/api/admin/props",methods=["GET","POST"])
@admin
def props():
    p=SERVER_DIR/"server.properties"
    if request.method=="GET":return jsonify(text=p.read_text(encoding="utf-8") if p.exists() else "")
    txt=(request.json or {}).get("text","").replace("\r\n","\n")
    if not txt.strip() or len(txt)>50000:return jsonify(error="Inhalt leer oder zu groß.")
    for i,line in enumerate(txt.split("\n"),1):
        if line.strip() and not line.lstrip().startswith("#") and not re.match(r"^[A-Za-z0-9._-]+=",line):return jsonify(error=f"Zeile {i} ist ungültig.")
    p.write_text(txt.rstrip("\n")+"\n",encoding="utf-8");return jsonify(ok=True)
@app.route("/api/admin/software")
@admin
def software():
    total=total_memory();return jsonify(version=server_version(),versions=paper_versions(),managed=True,ram_gb=ram_gb,max_gb=max(1,int(total/1024**3)-1),total_gb=round(total/1024**3,1))
@app.route("/api/admin/version",methods=["POST"])
@admin
def change_version():
    global ram_gb
    v=(request.json or {}).get("version","");vs=paper_versions()
    if v not in vs:return jsonify(error="Diese Paper-Version ist nicht verfügbar.")
    cur=server_version()
    if cur==v:return jsonify(error="Diese Version läuft bereits.")
    reset=(request.json or {}).get("reset_world",False)
    if cur!="unbekannt" and version_key(v)<version_key(cur) and not reset:return jsonify(error="Downgrade gesperrt. Für ein Downgrade musst du eine neue Welt erstellen.")
    def job():
        do_backup()
        if is_running():
            send_command("stop")
            for _ in range(90):
                if not is_running():break
                time.sleep(1)
        if reset:
            for w in world_names():shutil.rmtree(SERVER_DIR/w,ignore_errors=True)
            for cfg in ("config","paper-global.yml","paper-world.yml"):
                p=SERVER_DIR/cfg
                if p.is_dir():shutil.rmtree(p,ignore_errors=True)
                elif p.exists():p.unlink()
        old=JAR_PATH.with_suffix(".jar.old")
        if JAR_PATH.exists():shutil.copy2(JAR_PATH,old)
        download_paper_version(v)
        if is_running():raise RuntimeError("Serverprozess läuft noch.")
        start_server_process()
    return run_task(f"Version wird auf {v} gewechselt",job)
@app.route("/api/admin/ram",methods=["POST"])
@admin
def change_ram():
    global ram_gb
    try:g=int((request.json or {}).get("gb"))
    except Exception:return jsonify(error="Bitte eine ganze Zahl angeben.")
    mx=max(1,int(total_memory()/1024**3)-1)
    if not 1<=g<=mx:return jsonify(error=f"Du kannst 1 bis {mx} GB wählen.")
    def job():
        global ram_gb
        was=is_running()
        if was:
            send_command("stop")
            for _ in range(90):
                if not is_running():break
                time.sleep(1)
        ram_gb=g
        try:
            cfg=json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg["ram_gb"]=g
            CONFIG_PATH.write_text(json.dumps(cfg,indent=2),encoding="utf-8")
            CONFIG_PATH.chmod(0o600)
        except Exception: pass
        if was:start_server_process()
    return run_task(f"RAM wird auf {g} GB gesetzt",job)


@app.route("/api/admin/server-icon", methods=["GET"])
@admin
def server_icon_get():
    ensure_default_server_icon()
    try:
        raw = SERVER_ICON_PATH.read_bytes()
        return jsonify(ok=True, custom=raw != base64.b64decode(DEFAULT_SERVER_ICON_B64),
                       data="data:image/png;base64," + base64.b64encode(raw).decode("ascii"))
    except Exception as exc:
        return jsonify(error=f"Server-Icon konnte nicht gelesen werden: {exc}"), 500


@app.route("/api/admin/server-icon/upload", methods=["POST"])
@admin
def server_icon_upload():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="Bitte wähle zuerst ein Bild aus.")
    if Path(f.filename).suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        return jsonify(error="Erlaubt sind PNG-, JPG- und WebP-Bilder.")
    try:
        from PIL import Image, ImageOps
        f.stream.seek(0)
        with Image.open(f.stream) as source:
            image = ImageOps.fit(source.convert("RGBA"), (64, 64), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            buf = io.BytesIO()
            image.save(buf, format="PNG", optimize=True)
        tmp = SERVER_ICON_PATH.with_name("server-icon.png.part")
        tmp.write_bytes(buf.getvalue())
        tmp.replace(SERVER_ICON_PATH)
        return jsonify(ok=True, message="Server-Icon gespeichert. Starte den Minecraft-Server neu, damit die Änderung sichtbar wird.")
    except ImportError:
        return jsonify(error="Für die Bildverarbeitung fehlt Pillow. Installiere es mit: pip install Pillow"), 500
    except Exception as exc:
        return jsonify(error=f"Das Bild konnte nicht verarbeitet werden: {exc}"), 400


@app.route("/api/admin/server-icon/reset", methods=["POST"])
@admin
def server_icon_reset():
    try:
        SERVER_ICON_PATH.write_bytes(base64.b64decode(DEFAULT_SERVER_ICON_B64))
        return jsonify(ok=True, message="Standard-Server-Icon wiederhergestellt. Ein Server-Neustart ist erforderlich.")
    except Exception as exc:
        return jsonify(error=f"Standard-Icon konnte nicht wiederhergestellt werden: {exc}"), 500


@app.route("/api/admin/plugins")
@admin
def plugins():
    p=SERVER_DIR/"plugins";p.mkdir(exist_ok=True)
    return jsonify(files=[{"name":x.name,"mb":round(x.stat().st_size/1e6,2)} for x in sorted(p.glob("*.jar"),key=lambda x:x.name.lower())])
@app.route("/api/admin/plugins/upload",methods=["POST"])
@admin
def plugin_upload():
    f=request.files.get("file")
    if not f or not f.filename:return jsonify(error="Keine Datei ausgewählt.")
    name=re.sub(r"[^A-Za-z0-9._+-]","_",Path(f.filename.replace("\\","/")).name)
    if not PLNAME.fullmatch(name):return jsonify(error="Nur .jar-Dateien sind erlaubt.")
    p=SERVER_DIR/"plugins";p.mkdir(exist_ok=True);tmp=p/("."+name+".part");f.save(tmp)
    if not paper_plugin(tmp):tmp.unlink(missing_ok=True);return jsonify(error="Das ist kein Paper-/Bukkit-Plugin (plugin.yml fehlt).")
    tmp.replace(p/name);return jsonify(ok=True,message=f"{name} hochgeladen. Neustart erforderlich.")
@app.route("/api/admin/plugins/delete",methods=["POST"])
@admin
def plugin_delete():
    n=(request.json or {}).get("name","");p=SERVER_DIR/"plugins"/n
    if not PLNAME.fullmatch(n) or not p.is_file():return jsonify(error="Plugin nicht gefunden.")
    p.unlink();return jsonify(ok=True,message=f"{n} gelöscht.")
@app.route("/api/admin/reset_world",methods=["POST"])
@admin
def reset_world():
    seed=((request.json or {}).get("seed") or "").strip()
    if not re.fullmatch(r"[-A-Za-z0-9 _]{0,40}",seed):return jsonify(error="Ungültiger Seed.")
    def job():
        do_backup()
        was=is_running()
        if was:
            send_command("stop")
            for _ in range(90):
                if not is_running():break
                time.sleep(1)
        for w in world_names():shutil.rmtree(SERVER_DIR/w,ignore_errors=True)
        write_props({"level-seed":seed})
        if was:start_server_process()
    return run_task("Neue Welt wird erstellt",job)
@app.route("/api/admin/backup",methods=["POST"])
@admin
def backup():
    if task["name"]:return jsonify(error="Es läuft bereits eine Aufgabe.")
    return run_task("Backup wird erstellt",do_backup)
@app.route("/api/admin/backups")
@admin
def backups():
    return jsonify(busy=bool(task["name"] and "Backup" in task["name"]),files=[{"name":p.name,"mb":round(p.stat().st_size/1e6,1)} for p in sorted(BACKUP_DIR.glob("welt-*.tar.gz"),reverse=True)])
@app.route("/api/admin/backup/delete",methods=["POST"])
@admin
def backup_delete():
    n=(request.json or {}).get("name","")
    if not BKNAME.fullmatch(n) or not (BACKUP_DIR/n).is_file():return jsonify(error="Backup nicht gefunden.")
    (BACKUP_DIR/n).unlink();return jsonify(ok=True,message="Backup gelöscht.")
@app.route("/api/admin/restore",methods=["POST"])
@admin
def restore():
    n=(request.json or {}).get("name","")
    if not BKNAME.fullmatch(n) or not (BACKUP_DIR/n).is_file():return jsonify(error="Backup nicht gefunden.")
    def job():
        do_backup()
        was=is_running()
        if was:
            send_command("stop")
            for _ in range(90):
                if not is_running():break
                time.sleep(1)
        # Validate archive paths before extracting.
        with tarfile.open(BACKUP_DIR/n,"r:gz") as t:
            root=SERVER_DIR.resolve()
            for m in t.getmembers():
                target=(SERVER_DIR/m.name).resolve()
                if os.path.commonpath([str(root),str(target)])!=str(root):raise RuntimeError("Unsicherer Pfad im Backup.")
            for w in world_names():shutil.rmtree(SERVER_DIR/w,ignore_errors=True)
            t.extractall(SERVER_DIR,filter="data")
        if was:start_server_process()
    return run_task("Backup wird wiederhergestellt",job)
@app.route("/admin/backup/<name>")
@admin
def download_backup(name):
    if not BKNAME.fullmatch(name):abort(404)
    return send_file(BACKUP_DIR/name,as_attachment=True)

@app.errorhandler(413)
def too_big(e):return jsonify(error="Die Datei ist zu groß (maximal 200 MB)."),413

def graceful_stop(timeout=75):
    """Sendet stop und wartet auf das Speichern/Beenden des Minecraft-Prozesses."""
    global mc_process
    proc = mc_process
    if proc is None or proc.poll() is not None:
        return
    try:
        send_command("stop")
    except Exception:
        pass
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            print("[!] Minecraft reagiert nicht auf stop; Prozess wird beendet.")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


_shutdown_lock = threading.Lock()
_shutdown_started = False

def shutdown_handler(*_args):
    """Idempotenter Shutdown für Signale und atexit."""
    global _shutdown_started
    with _shutdown_lock:
        if _shutdown_started:
            return
        _shutdown_started = True
    graceful_stop()


def handle_signal(_signum, _frame):
    shutdown_handler()
    raise SystemExit(0)


atexit.register(shutdown_handler)
for _sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
    if _sig is not None:
        try:
            signal.signal(_sig, handle_signal)
        except (ValueError, OSError):
            pass


def create_tray_image():
    """Lädt das aktuelle PrivateMC-Icon für den Windows/Linux-System-Tray."""
    if Image is None:
        return None
    try:
        ensure_default_server_icon()
        with Image.open(SERVER_ICON_PATH) as source:
            return source.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
    except Exception:
        if ImageDraw is None:
            return None
        image = Image.new("RGBA", (64, 64), (20, 28, 38, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((3, 3, 61, 61), radius=13, fill=(240, 166, 58, 255))
        draw.text((16, 13), "M", fill=(20, 28, 38, 255), stroke_width=1)
        return image


def configure_windows_autostart():
    """Registriert die gepackte Windows-EXE für den Autostart des aktuellen Benutzers."""
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return
    try:
        import winreg
        run_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\Run")
        try:
            # Anführungszeichen sind wichtig, falls der Installationspfad Leerzeichen enthält.
            winreg.SetValueEx(run_key, "PrivateMC", 0, winreg.REG_SZ, f'"{Path(sys.executable).resolve()}"')
        finally:
            winreg.CloseKey(run_key)
        print("[✓] Windows-Autostart für den aktuellen Benutzer eingerichtet.")
    except Exception as exc:
        raise RuntimeError(f"Windows-Autostart konnte nicht eingerichtet werden: {exc}") from exc


def _windows_message_box(text, title, flags):
    """Zeigt einen nativen Windows-Dialog, auch wenn die EXE ohne Konsole läuft."""
    import ctypes
    return ctypes.windll.user32.MessageBoxW(None, text, title, flags)


def uninstall_windows(icon, _item=None):
    """Entfernt PrivateMC aus dem Autostart und löscht die EXE nach dem Beenden."""
    if os.name != "nt" or not getattr(sys, "frozen", False):
        _windows_message_box(
            "Die automatische Deinstallation ist nur in der Windows-EXE verfügbar.",
            "PrivateMC", 0x00000040)
        return

    script_dir = Path(tempfile.gettempdir())
    prompt_script = script_dir / f"PrivateMC-prompt-{os.getpid()}.ps1"
    
    # Umlaute wurden hier sauber auf ae, oe, ue, ss umgestellt, 
    # damit es in PowerShell-Skripten plattformunabhängig fehlerfrei angezeigt wird.
    prompt_code = """
    Add-Type -AssemblyName PresentationFramework
    $ans1 = [System.Windows.MessageBox]::Show(
        "PrivateMC wird beendet und aus dem Windows-Autostart entfernt.\\n\\nDie PrivateMC.exe wird anschliessend geloescht.\\nDeine Minecraft-Welten, Backups und Einstellungen bleiben erhalten.\\n\\nMoechtest du fortfahren?",
        "PrivateMC deinstallieren",
        [System.Windows.MessageBoxButton]::YesNo,
        [System.Windows.MessageBoxImage]::Question
    )
    if ($ans1 -ne 'Yes') { exit 1 }

    $ans2 = [System.Windows.MessageBox]::Show(
        "Sollen zusaetzlich ALLE PrivateMC-Daten geloescht werden?\\n\\nDas umfasst Minecraft-Serverdateien, Welten, Backups, Java und Einstellungen.\\nDiese Loeschung kann nicht rueckgaengig gemacht werden.\\n\\nJa = alles loeschen; Nein = Daten behalten.",
        "PrivateMC-Daten loeschen?",
        [System.Windows.MessageBoxButton]::YesNo,
        [System.Windows.MessageBoxImage]::Question
    )
    $deleteData = ($ans2 -eq 'Yes')
    [System.IO.File]::WriteAllText($args[0], "$deleteData")
    exit 0
    """
    
    result_flag_path = script_dir / f"PrivateMC-result-{os.getpid()}.txt"
    if result_flag_path.exists():
        result_flag_path.unlink()

    prompt_script.write_text(prompt_code, encoding="utf-8")

    try:
        process = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(prompt_script), str(result_flag_path)],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if prompt_script.exists():
            prompt_script.unlink()

        if process.returncode != 0 or not result_flag_path.exists():
            return

        delete_data = result_flag_path.read_text(encoding="utf-8").strip().lower() == "true"
        if result_flag_path.exists():
            result_flag_path.unlink()

        exe_path = Path(sys.executable).resolve()
        data_path = BASE_DIR.resolve()
        script_path = script_dir / f"PrivateMC-uninstall-{os.getpid()}.ps1"

        def ps_quote(value):
            return "'" + str(value).replace("'", "''") + "'"

        script_lines = [
            f"$exePath = {ps_quote(exe_path)}",
            f"$dataPath = {ps_quote(data_path)}",
            f"$deleteData = ${str(delete_data).lower()}",
            "Start-Sleep -Seconds 2",
            "while ([System.IO.File]::Open($exePath, 'Open', 'Write', 'None') -eq $null) { Start-Sleep -Milliseconds 500 }",
            "Remove-Item -LiteralPath $exePath -Force -ErrorAction SilentlyContinue",
            "if ($deleteData) { Remove-Item -LiteralPath $dataPath -Recurse -Force -ErrorAction SilentlyContinue }",
            "Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue",
        ]
        script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8-sig")

        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                                winreg.KEY_SET_VALUE) as run_key:
                try:
                    winreg.DeleteValue(run_key, "PrivateMC")
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            pass

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
             "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)

        def finish_uninstall():
            try:
                graceful_stop(timeout=10)
            finally:
                try:
                    icon.stop()
                except Exception:
                    pass
                os._exit(0)

        threading.Thread(target=finish_uninstall, name="PrivateMC-uninstall", daemon=True).start()
    except Exception as exc:
        _windows_message_box(
            "Die Deinstallation konnte nicht gestartet werden.\n\n"
            f"Fehler: {exc}\n\n"
            "PrivateMC läuft weiterhin. Bitte versuche es erneut.",
            "PrivateMC – Deinstallationsfehler", 0x00000010)


# ============================================================
# TRAY-START & PROGRAMMSTART (KORRIGIERT FÜR WINDOWS & LINUX)
# ============================================================

def run_tray_and_flask(host, port):
    """
    Steuert den plattformunabhängigen Start. 
    Auf Windows blockiert das Tray den Hauptthread, auf Headless-Linux startet nur Flask.
    """
    global pystray, Image, ImageDraw

    # Prüfen, ob wir eine grafische Oberfläche haben (wichtig für Linux Server)
    has_display = (
        os.name == "nt"
        or bool(os.environ.get("DISPLAY"))
        or bool(os.environ.get("WAYLAND_DISPLAY"))
    )

    if pystray is not None and Image is not None and ImageDraw is not None and has_display:
        print("[✓] Grafische Oberfläche erkannt. Starte Webserver im Hintergrund und aktiviere System-Tray...")
        
        # 1. Flask in einen separaten Hintergrund-Thread auslagern
        flask_thread = threading.Thread(
            target=lambda: app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False),
            daemon=True,
            name="flask-webserver"
        )
        flask_thread.start()

        # 2. Das System-Tray-Icon MUSS zwingend im Hauptthread laufen (Windows-Pflicht!)
        def open_admin(_icon, _item):
            webbrowser.open(f"http://127.0.0.1:{WEB_PORT}/admin")

        def quit_app(icon, _item):
            graceful_stop(timeout=75)
            try: icon.stop()
            except Exception: pass
            os._exit(0)

        menu_items = [pystray.MenuItem("Admin-Panel öffnen", open_admin)]
        if os.name == "nt" and getattr(sys, "frozen", False):
            menu_items.append(pystray.MenuItem("PrivateMC deinstallieren...", uninstall_windows))
        menu_items.append(pystray.MenuItem("Server beenden", quit_app))
        menu = pystray.Menu(*menu_items)
        icon = pystray.Icon("PrivateMC", create_tray_image(), "PrivateMC Server", menu)
        
        # icon.run() blockiert ab hier den Hauptthread sauber auf Windows
        icon.run()
    else:
        # FALLBACK FÜR DEIN UBUNTU SERVER (Headless / Ohne Desktop)
        print("[!] Kein Desktop erkannt oder Bibliotheken fehlen. Überspringe System-Tray.")
        print(f"[✓] Starte Webserver direkt im Hauptthread...")
        app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)


if __name__ == "__main__":
    try:
        # Sichtbares Setupfenster für die erste Windows-Installation.
        has_gui = (
            os.name == "nt"
            or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        )
        java_ready = (
            bool(find_portable_java())
            or bool(shutil.which("java") and (get_java_major(shutil.which("java")) or 0) >= JAVA_VERSION)
        )
        paper_ready = JAR_PATH.exists() and JAR_PATH.stat().st_size > 1024 * 1024
        if has_gui and getattr(sys, "frozen", False) and not (java_ready and paper_ready):
            import tkinter as tk
            from tkinter import ttk, messagebox
            import queue
            q = queue.Queue()
            root = tk.Tk()
            root.title("PrivateMC – Ersteinrichtung")
            root.geometry("490x190")
            root.resizable(False, False)
            root.attributes("-topmost", True)
            root.protocol("WM_DELETE_WINDOW", lambda: None)
            ttk.Label(root, text="PrivateMC wird eingerichtet", font=("TkDefaultFont", 13, "bold")).pack(pady=(18, 6))
            status = ttk.Label(root, text="Java wird geprüft bzw. installiert …")
            status.pack(pady=4)
            bar = ttk.Progressbar(root, mode="indeterminate", length=400)
            bar.pack(pady=10)
            ttk.Label(root, text="Downloads und Einrichtung können einige Minuten dauern.").pack()
            bar.start(10)
            def setup_worker():
                try:
                    q.put(("status", "Java wird geprüft bzw. installiert …"))
                    setup_java()
                    q.put(("status", "Paper-Minecraft-Server wird heruntergeladen …"))
                    setup_paper()
                    q.put(("status", "PrivateMC wird vorbereitet …"))
                    configure_windows_autostart()
                    q.put(("done", None))
                except BaseException as exc:
                    q.put(("error", exc))
            threading.Thread(target=setup_worker, daemon=True, name="PrivateMC-setup").start()
            def poll_setup():
                try:
                    while True:
                        kind, value = q.get_nowait()
                        if kind == "status":
                            status.configure(text=value)
                        elif kind == "done":
                            bar.stop()
                            root.destroy()
                            return
                        elif kind == "error":
                            bar.stop()
                            root.destroy()
                            if isinstance(value, SystemExit):
                                raise value
                            messagebox.showerror("PrivateMC – Einrichtungsfehler", str(value))
                            raise SystemExit(1)
                except queue.Empty:
                    pass
                root.after(150, poll_setup)
            root.after(150, poll_setup)
            root.mainloop()
            # Tkinter-Dialoge (insbesondere die EULA-Abfrage) laufen erst nach
            # Schließen des Fortschrittsfensters im Hauptthread.
            if not request_eula_consent():
                print("Setup ohne EULA-Zustimmung beendet.")
                sys.exit(1)
        else:
            setup_java()
            setup_paper()
            if not request_eula_consent():
                print("Setup ohne EULA-Zustimmung beendet.")
                sys.exit(1)
            configure_windows_autostart()

    except SystemExit:
        raise
    except Exception as e:
        print("[X] Setup fehlgeschlagen:", e)
        has_gui = (
            os.name == "nt"
            or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        )
        if has_gui and (getattr(sys, "frozen", False) or sys.stdin is None):
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("PrivateMC – Einrichtungsfehler", str(e), parent=root)
                root.destroy()
            except Exception:
                pass
        sys.exit(1)

    host = os.environ.get("MC_BIND", "0.0.0.0")
    port = WEB_PORT
    print(f"\nWebsite/Admin-Panel active under: http://127.0.0.1:{port}")
    print(f"In local network: http://<IP-DES-RECHNERS>:{port}")
    print("Minecraft files located in:", SERVER_DIR)
    print("="*60 + "\n")

    try:
        # Startet den intelligenten Weichensteller für Tray/Flask
        run_tray_and_flask(host, port)
    finally:
        shutdown_handler()
