import lark

# On définit la grammaire de notre mini-c

grammaire = lark.Lark(r"""
exp : SIGNED_NUMBER                     -> exp_nombre
| IDENTIFIER                            -> exp_var
| exp OPBIN exp                         -> exp_opbin
| "(" exp ")"                           -> exp_par
| POINTEUR IDENTIFIER                      -> exp_pointeur


com : LEFT "=" exp ";"            -> assignation
| "if" "(" exp ")" "{" bcom "}"         -> if
| "while" "(" exp ")" "{" bcom "}"      -> while
| "print" "(" exp ")"                   -> print
| TYPE IDENTIFIER ";"                   -> declaration

bcom : (com)*
prg : INTORVOID "main" "(" var_list ")" "{" bcom "return" "(" exp ")" ";" "}"


var_list :                              -> vide
| "int argc, char** argv"       -> non_vide
| "void"                               -> vide

IDENTIFIER : /[a-zA-Z][a-zA-Z0-9]*/
STAR : /(\*)+/
LEFT_IDENTIFIER : IDENTIFIER | STAR IDENTIFIER
LEFT : LEFT_IDENTIFIER |  STAR "(" LEFT_IDENTIFIER + SIGNED_NUMBER ")"

INTORVOID : "int" | "void"

POINTEUR : /(&)?(\*)+/ | /(&)/



OPBIN : /[+*\->]/

TYPE : /(int|char)[*]*/



%import common.WS
%import common.SIGNED_NUMBER
%ignore WS
""",
start = "prg")

op = { '+' : "add", '-' : "sub"}



ast = grammaire.parse("""void main(int argc, char** argv) {

    int y;
    y=4;

    int a;
    a = &y;

    return(a);
}
""")


def asm_exp(e) :
    if e.data == "exp_nombre":
        return f"mov rax, {e.children[0].value}\n"
    elif e.data == "exp_var":
        return f"mov rax, [{e.children[0].value}]\n"
    elif e.data == "exp_par":
        # Il suffit de compiler ce qu'il y a à l'intérieur des parenthèses
        return asm_exp(e.children[0])
    elif e.data == "exp_pointeur":

        # Ne gère pas les pointeurs sur des pointeurs

        toSplit = e.children[0].value
        for c in toSplit:
            if c == "*":
                result = f"mov rax, [{e.children[1]}]\n"
            elif c == "&":
                result = f"mov rax, {e.children[1]}\n"




        return result

    elif e.data == "exp_opbin":
        E1 = asm_exp(e.children[0]) # Pour que ce soit plus lisible
        E2 = asm_exp(e.children[2])
        return f"""
        {E2}
        push rax
        {E1}
        pop rbx
        {op[e.children[1].value]} rax,rbx
        """ # NB : Pour l'instant on s'occupe uniquement de l'opération
    else:
        return "error asm_exp"

def vars_exp(e) :


    if e.data == "exp_nombre":
        return set()
    elif e.data == "exp_var":
        return {e.children[0].value}
    elif e.data == "exp_par":
        return vars_exp(e.children[0])
    elif e.data == "exp_opbin":
        # L'union de L et de R
        return vars_exp(e.children[0]) | vars_exp(e.children[2])
    elif e.data == "exp_pointeur":
        print("probleme")
        print(e.children[1])
        return {e.children[1]}



def pp_exp(e) :
    if e.data in {"exp_nombre", "exp_var"} :
        return e.children[0].value
    elif e.data == "exp_par":
        return f"({pp_exp(e.children[0])})"
    elif e.data == "exp_opbin":
        return f"{pp_exp(e.children[0])} {e.children[1].value} {pp_exp(e.children[2])}"
    elif e.data == "exp_pointeur":
        return f"{e.children[0].value}{(e.children[1])}"


def pp_com(c) :
    if c.data == "assignation":
        return f"{c.children[0]} = {pp_exp(c.children[1])};"
    elif c.data == "if":
        return f"if ({pp_exp(c.children[0])}) {{ {pp_bcom(c.children[1])} }}"
    elif c.data == "while":
        return f"while ({pp_exp(c.children[0])}) {{ {pp_bcom(c.children[1])}}}"
    elif c.data == "print":
        return f"print({pp_exp(c.children[0])})"
    elif c.data == "declaration":
        return f"{c.children[0]} {c.children[1]};"

def vars_com(c) :
    if c.data == "assignation":
        R = vars_exp(c.children[1]) # Donne toutes les variables qu'il y a dans l'expression
        return {c.children[0].value} | R
    elif c.data in {"if", "while"} :
        B = vars_bcom(c.children[1])
        E = vars_exp(c.children[0])
        return B | E
    elif c.data == "print":
        return vars_exp(c.children[0])
    elif c.data == "declaration":
        return {c.children[1].value}



cpt = 0 # Compteur pour le nombre de fonctions fin
def next() :
    global cpt
    cpt += 1
    return cpt

def asm_com(c) :
    if c.data == "assignation":
        E = asm_exp(c.children[1])
        return f"""
        {E}
        mov [{c.children[0].value}], rax
        """
    elif c.data == "if":
        E = asm_exp(c.children[0])
        C = asm_bcom(c.children[1])
        n = next()
        return f"""
        {E}
        cmp rax,0
        jz fin{n}
        {C}
fin{n} : nop"""
    elif c.data == "while":
        E = asm_exp(c.children[0])
        C = asm_bcom(c.children[1])
        n = next()
        return f"""
        debut{n} : {E}
        cmp rax,0
        jz fin{n}
        {C}
        jmp debut{n}
fin{n} : nop"""
    elif c.data == "print":
        E = asm_exp(c.children[0])
        return f"""
        {E}
        mov rdi, fmt
        mov rsi, rax
        call printf
        """
    elif c.data == "declaration":
        return ""


def pp_bcom(bc) :
    return "\n"  + "\n".join([pp_com(c) for c in bc.children]) +"\n"

def vars_bcom(bc) :
    S = set()

    for c in bc.children :
        S = S | vars_com(c)
    return S

def asm_bcom(bc) :
    return "\n"  + "".join([asm_com(c) for c in bc.children]) +"\n" # En fait on a déjà mis des /n dans les autres fonctions

def vars_prg(p) :
    print(p.pretty())
    # L = set([t.value for t in p.children[0].children])
    C = vars_bcom(p.children[2])
    R = vars_exp(p.children[3])
    return  C | R

def pp_prg(p) :
    TYPE = p.children[0]
    L = pp_var_list(p.children[1])
    C = pp_bcom(p.children[2])
    R = pp_exp(p.children[3])
    return "%s main (%s) {%s return (%s);\n}" % (TYPE,L,C,R)

def asm_prg(p) :
    f = open("moule.asm")
    moule = f.read()
    C = asm_bcom(p.children[2])
    moule = moule.replace("BODY", C)
    R = asm_exp(p.children[3])
    moule = moule.replace("RETURN", R)
    D = "\n".join([f"{v} : dq 0" for v in vars_prg(p)])
    moule = moule.replace("DECL_VARS", D)
    s = ""
    print(p.children[2].pretty())
    for i in range(len(p.children[1].children)) :
        v = p.children[1].children[i].value
        e = f"""
        mov rbx, [argv]
        mov rdi, [rbx+{8*(i+1)}]
        xor rax,rax
        call atoi
        mov [{v}], rax
        """
        s = s+e
    moule = moule.replace("INIT_VARS", s)

    f = open("prog.asm", "w")
    f.write(moule)
    f.close()
    return moule

def pp_var_list(vl) :
    print(vl)
    if vl.data == "non_vide":
        return "int argc, char** argv"
    if vl.data == "vide":
        return ""




# print(pp_exp(ast))
#print(asm_prg(ast))

# print(ast.pretty())
asm_prg(ast)


# asm = asm_prg(ast)
# f = open("ouf.asm", "w")
# f.write(asm)
# f.close()
