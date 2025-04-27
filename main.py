import os, sys, time, random

script = os.path.basename(sys.argv[0])
if script.lower().startswith('curses'):
    print('Error: Rename this script to matrix.py to avoid curses module conflict.')
    sys.exit(1)
try:
    import curses
except ImportError:
    try:
        import windows_curses as curses
    except ImportError:
        print('Error: curses module not found. On Windows install windows-curses: pip install windows-curses')
        sys.exit(1)

SPEED_BASE=0.01
DENSITY=0.04
GLITCH_FREQ=0.003
LINE_GLITCH_FREQ=0.1
LOG_LINE_FREQ=0.4
ERROR_FREQ=0.2
TICKER_GLITCH_FREQ=0.005
ANIM_STEPS=30
ANIM_DELAY=0.01

CHARS='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@#$%^&*(){}[]<>|'
GLITCH_CHARS='~!@#$%^&*()_+-=[]{};:,.<>?'
BLOCK_CHAR=' '

HEADLINES=[
    'SECURITY ALERT: Zero-Day Exploit Detected',
    'BREACH: Unauthorized Access to Secure Server',
    'PATCH RELEASED: CVE-2025-1234 Fixed',
    'RANSOMWARE: Files Encrypted on Host 10.0.0.5',
    'MALWARE PROPAGATION: Worm Spread in Network',
    'INTRUSION: Suspicious Login from TOR Node',
]
LOG_TEMPLATES=[
    "[AUTH] Failed login for user '{user}' from {ip}:{port}",
    "[SSH] Connection closed by {ip}:{port}",
    "[HTTP] 401 Unauthorized on /admin from {ip}",
    "[MALWARE] Trojan.{trojan} detected in /usr/bin/{file}",
    "[IDS] Alert {sig} matched on {iface}",
    "[NET] SYN flood from {ip}, count={count}",
    "[DB] DROP TABLE {table} by {user}@{ip}",
    "[CRYPTO] Hash collision {hash}",
    "[KERN] Oops in {module} at {addr:#x}",
    "[PATCH] Applied {patch}",
    "[PKG] Installed {package}-{ver}",
]
USERS=['root','admin','guest','postgres']
PORTS=[22,80,443,3306]
IPS=['192.168.1.%d'%i for i in range(1,50)]
TROJANS=['Emotet','Zeus','Mirai']
FILES=['ssh','kernel','syslog']
SIGS=['SQL_INJECTION','XSS_ATTACK','PORT_SCAN']
IFACES=['eth0','wlan0']
TABLES=['users','sessions']
MODULES=['fs','netfilter']
PATCHES=['CVE-2025-1234']
PACKAGES=['openssl','curl']

class Matrix:
    def __init__(self, stdscr):
        self.stdscr=stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1,curses.COLOR_GREEN,-1)
        curses.init_pair(2,curses.COLOR_WHITE,-1)
        curses.init_pair(3,curses.COLOR_RED,-1)
        curses.init_pair(4,curses.COLOR_YELLOW,-1)
        curses.init_pair(5,curses.COLOR_CYAN,-1)
        curses.init_pair(6,curses.COLOR_BLACK,curses.COLOR_RED)
        curses.init_pair(7,curses.COLOR_BLACK,curses.COLOR_BLACK)
        self.full_mode=False
        self.animating=False
        self.frame=0
        self.ticker=' *** '.join(HEADLINES)+'   '
        self.tpos=0
        self.errs=[]
        self.resize()
    def resize(self,*_):
        self.height,self.width=self.stdscr.getmaxyx()
        max_log=min(60,self.width//3)
        if not self.animating:
            self.log_w=0 if self.full_mode else max_log
        self.mx0=self.log_w+2 if self.log_w>0 else 0
        self.matrix_y0=1
        self.matrix_h=self.height-2
        self.drops=[0]*self.width
        self.speeds=[random.uniform(SPEED_BASE*0.5,SPEED_BASE*1.5) for _ in range(self.width)]
        t0=time.time()
        self.next_time=[t0+random.random()*s for s in self.speeds]
        self.log_lines=['']*(self.height-2)
    def gen_log(self):
        tmpl=random.choice(LOG_TEMPLATES)
        return tmpl.format(
            user=random.choice(USERS),ip=random.choice(IPS),port=random.choice(PORTS),
            trojan=random.choice(TROJANS),file=random.choice(FILES),sig=random.choice(SIGS),
            iface=random.choice(IFACES),count=random.randint(100,2000),table=random.choice(TABLES),
            hash=hex(random.getrandbits(32)),module=random.choice(MODULES),addr=random.randint(0,0xFFFFF),
            patch=random.choice(PATCHES),package=random.choice(PACKAGES),ver=f"{random.randint(1,2)}.{random.randint(0,9)}"
        )
    def gen_error(self):
        text=f"[ERROR] Critical fault at sector {random.randint(0,255)}"
        x=random.randint(self.mx0,self.width-len(text)-1)
        y=random.randint(2,self.height-3)
        return[text,x,y,random.randint(20,50)]
    def animate_toggle(self):
        self.animating=True
        max_log=min(60,self.width//3)
        start,end=(0,max_log) if self.full_mode else (max_log,0)
        widths=[int(start+(end-start)*i/ANIM_STEPS) for i in range(ANIM_STEPS+1)]
        for w in widths:
            self.log_w=w
            self.mx0=self.log_w+2 if w>0 else 0
            self.stdscr.erase()
            self.draw()
            time.sleep(ANIM_DELAY)
        self.full_mode=not self.full_mode
        self.resize()
        self.animating=False
    def draw(self):
        cpu=random.randint(0,100); mem=random.randint(0,100)
        ts=time.strftime('%H:%M:%S')
        cm=f"CPU:{cpu:02d}% MEM:{mem:02d}%"
        reserved=len(cm)+len(ts)+2
        seg_w=self.width-reserved
        ticker_disp=(self.ticker+' '*self.width)
        segment=ticker_disp[self.tpos:self.tpos+seg_w]
        for i,ch in enumerate(segment):
            attr=curses.color_pair(3)|curses.A_BOLD if random.random()<TICKER_GLITCH_FREQ else curses.color_pair(5)|curses.A_BOLD
            self.safe_add(0,i,ch,attr)
        self.safe_add(0,seg_w,' '+cm,curses.color_pair(2)|curses.A_BOLD)
        self.safe_add(0,seg_w+len(cm)+1,ts,curses.color_pair(5)|curses.A_BOLD)
        self.tpos=(self.tpos+1)%len(self.ticker)
        if not self.full_mode and random.random()<LOG_LINE_FREQ:
            self.log_lines=[self.gen_log()]+self.log_lines[:-1]
        for idx,line in enumerate(self.log_lines):
            y=idx+1
            txt=line.ljust(self.log_w)[:self.log_w]
            if '[ERROR]' in line or '[MALWARE]' in line or '[CRYPTO]' in line or '[KERN]' in line:
                attr=curses.color_pair(3)
            elif '[WARNING]' in line:
                attr=curses.color_pair(4)
            elif any(p in line for p in ['[AUTH]','[SSH]','[HTTP]','[IDS]','[NET]','[DB]','[PATCH]','[PKG]']):
                attr=curses.color_pair(5)
            else:
                attr=curses.color_pair(2)
            self.safe_add(y,0,txt,attr)
            if self.log_w>0: self.safe_add(y,self.log_w,'|',curses.color_pair(5)|curses.A_BOLD)
        now=time.time()
        for x in range(self.mx0,self.width):
            if now<self.next_time[x]: continue
            l=self.drops[x]
            if l==0 and random.random()<DENSITY:
                self.drops[x]=1;l=1
            if l>0:
                for i in range(min(l,self.matrix_h)):
                    ch=random.choice(CHARS)
                    y=self.matrix_y0+i
                    attr=curses.color_pair(2)|curses.A_BOLD if i==l-1 else curses.color_pair(1)|(curses.A_DIM if l-i>4 else curses.A_NORMAL)
                    self.safe_add(y,x,ch,attr)
                self.drops[x]+=1
                if self.drops[x]>self.matrix_h+random.randint(0,8): self.drops[x]=0
            self.next_time[x]=now+self.speeds[x]
        if random.random()<GLITCH_FREQ:
            gy=random.randint(1,self.height-3)
            for _ in range(random.randint(5,20)): self.safe_add(random.randint(1,self.height-3),random.randint(self.mx0,self.width-1),random.choice(GLITCH_CHARS),curses.color_pair(3)|curses.A_REVERSE)
        if random.random()<LINE_GLITCH_FREQ:
            gy=random.randint(1,self.height-3)
            for x in range(self.mx0,self.width): self.safe_add(gy,x,random.choice(GLITCH_CHARS),curses.color_pair(3)|curses.A_REVERSE)
        if random.random()<ERROR_FREQ: self.errs.append(self.gen_error())
        for err in self.errs[:]:
            txt,x,y,ttl=err
            self.safe_add(y,x,txt,curses.color_pair(3)|curses.A_BLINK)
            err[3]-=1
            if err[3]<=0: self.errs.remove(err)
        for x in range(self.width):
            pat=(self.frame+x//3)%2
            color=(6 if pat else 7)
            self.safe_add(self.height-1,x,BLOCK_CHAR,curses.color_pair(color))
        self.frame+=1
        self.stdscr.refresh()
    def safe_add(self,y,x,s,a):
        try: self.stdscr.addstr(y,x,s,a)
        except: pass
    def run(self):
        while True:
            if not self.animating: self.stdscr.erase()
            self.draw()
            time.sleep(SPEED_BASE)
            c=self.stdscr.getch()
            if c==curses.KEY_RESIZE and not self.animating: self.resize()
            elif c==ord(' ') and not self.animating: self.animate_toggle()
            elif c!=-1 and not self.animating: break

def main():
    stdscr=None
    try:
        stdscr=curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        matrix=Matrix(stdscr)
        matrix.run()
    finally:
        if stdscr:
            stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

if __name__=='__main__':
    main()
