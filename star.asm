extern printf, atoi

section .data
fmt : db "%d", 10, 0
argc : dq 0
argv : dq 0
y : dq 0
a : dq 0

section .text
global main
main : 
    push rbp
    mov [argc], rdi
    mov [argv], rsi
    
    

            mov rax, 4

            mov [y], rax
            
            mov rax, [y]
mov rax, [y]

            mov [a], rax
            

    mov rax, [a]

    mov rdi, fmt
    mov rsi, rax
    call printf
    pop rbp
    ret
