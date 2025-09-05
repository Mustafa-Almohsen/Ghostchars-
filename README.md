# Ghostchars 🎴🔰
zwbypass is a Python CLI tool for obfuscating strings with invisible zero-width characters and homoglyphs, detecting them, and stripping them. It’s designed for authorized security testing, bug bounty hunters, and developers who want to test input validation, WAF filters, or normalization issues.
<img width="1337" height="436" alt="image" src="https://github.com/user-attachments/assets/0c090235-b417-4de7-80b5-54bf5d2a775b" />

----------------------------------
🟢 This tool can do the following:

🌀Insert Zero Width Space (U+200B), Zero Width Non-Joiner (U+200C), and Zero Width Joiner (U+200D) into strings.

🌀Replace letters with look-alike homoglyphs (Cyrillic/Greek).

🌀Detect and visualize zero-width characters in inputs.

🌀Strip zero-width characters to normalize inputs.

🌀Generate payloads to test filter bypasses, signup flows, WAFs, and input validation.

------------------------------

🩻 What’s the use cases of this tool in real world⁉️                                                                                                                                                                     
Great question! this method (zero-width + homoglyph injections) has some very real bug bounty / red team use cases, and zwbypass tool makes it much easier to test them. Let me break it down into offensive use cases (for hunters) and than defensive (for devs/security teams):

🟢 Offensive Bug Hunting Use Cases

1️⃣. WAF / Filter Bypasses

🌀Many WAFs and input validators just do a substring match for dangerous words like:

🌀admin, select, script, union

🌀Inserting a​d​m​i​n (with zero-width chars) or ѕcript (with homoglyphs) defeats simple string checks but backend parsers ignore the hidden chars, interpreting it as the original word.

🌀Use case: SQLi / XSS filter evasion

🌀sel​ect * from users bypasses naive SQL filters.

🌀<scr​ipt>alert(1)</scr​ipt> bypasses XSS filters.

2️⃣. Authentication & Authorization Bypasses

🌀Some apps block usernames like admin but don’t normalize input.

🌀Registering adm​in may bypass the restriction, yet backend treats it as the same user.

🌀Possible outcomes: Duplicate accounts for protected names. Account takeover or privilege escalation.

3️⃣. Path Traversal / File Upload Tricks

🌀Blacklists that forbid ../ or certain file extensions may fail if obfuscated:

🌀..%E2%80%8F/ (dir traversal bypass).

🌀shell.p​hp (bypasses extension checks, but server executes as PHP).

4️⃣. Keyword Blacklist Evasion in SSRF / LFI

🌀Apps may block http://127.0.0.1/ → bypass with 127.​0.0.1.

🌀Blocked word passwd → pas​swd still matches /etc/passwd.

⛔️ Defensive & Detection Use Cases ⛔️

Zwbypass tool is not only for bypassing, but also for testing and defending:

🌀 Quickly scan responses/inputs for hidden characters with --mode detect.

🌀 Normalization in pipelines: Use --mode strip to sanitize logs, usernames, or parameters before matching.

🌀 Hardening filters: Test a WAF/rule with obfuscated payloads to see if it actually normalizes properly.

-----------------------------------------------------------------------

🔴 Usage of tool:

Here is outputs for each mode of the tool so you can see exactly what’s happening. I’ll use the input string "admin" and "script" as examples.
1. Mode: every                                                                                                                                                                                                            
Command: ./zwbypass.py -i "admin" --mode every --zw zwsp
Output: a​d​m​i​n   ---> (that’s "admin" but with U+200B zero-width spaces between each character - well yes, it is looks identical on screen!👉 because the zero-width space (ZWSP) is invisible.
If we add --encode: a%E2%80%8Bd%E2%80%8Bm%E2%80%8Bi%E2%80%8Bn

2. Mode: random                                                                                                                                                                                                           
Command: ./zwbypass.py -i "script" --mode random --prob 0.5 --zw zwnj                                                                                                                                                     
Possible output (random each run, ~50% chance between characters):
Output: s​cr​i​pt   --->  (where the U+200C Zero Width Non-Joiner was injected a few times). ---->  Encoded: s%E2%80%8Ccr%E2%80%8Ci%E2%80%8Cpt


2.2 Mode: random 

./zwbypass.py -i $'admin' --mode random --encode --prob 0.4                                                                                                                                                               
Output: adm%E2%80%8Bin                                                                                                                                                                                                                                                                                                                                                                                                                           # So 👉 %E2%80%8B 👉 decoded 👉 'balnk​' (but you won’t see it since it’s invisible). 👉 I suggest to used for Obfuscation purposes: In URLs, or filenames/words to bypass filters.                                     


4.  Mode: keywords                                                                                                                                                                                                        
Command: ./zwbypass.py -i "user=admin&role=user" --mode keywords --keywords admin,role --zw zwsp                                                                                                                          
Output: user=a​d​m​i​n&r​o​l​e=user ---> (admin and role split by zero-width spaces, rest untouched). ----> Encoded: user=a%E2%80%8Bd%E2%80%8Bm%E2%80%8Bi%E2%80%8Bn&r%E2%80%8Bo%E2%80%8Bl%E2%80%8Be=user

5. Mode: homoglyphs                                                                                                                                                                                                       
Command: ./zwbypass.py -i "script" --mode homoglyphs                                                                                                                                                                      
Output: sсrірт ---> Notice: s replaced with Cyrillic 'ѕ' (U+0455) and  'c' replaced with Cyrillic с (U+0441) and 'i' replaced with Cyrillic і (U+0456) - Other letters stay the same. Looks identical but isn’t.

6.  Mode: detect                                                                                                                                                                                                           
Command: ./zwbypass.py -i $'adm\u200bin' --mode detect                                                                                                                                                                    
Output:  adm[ZWSP](U+200B)in   Zero-width positions:   - index 3: U+200B ZERO WIDTH SPACE

7. Mode: strip                                                                                                                                                                                                            
Command: ./zwbypass.py -i $'adm\u200bin' --mode strip    
Output: admin ---> (The hidden U+200C ZWNJ is gone, string normalized).                                                                                                                                                                                                                                                                                                                                                                                                                                                         
 8. ./zwbypass.py -i $'\u200b' --mode detect                                                                                                                                                                              
[ZWSP](U+200B)

Zero-width positions:
  - index 0: U+200B ZERO WIDTH SPACE                                                                                                                                                                                      
    

9. ./zwbypass.py -i $'..\u200b' --encode                                                                                                                                                                                    ..%E2%80%8B

10. ./zwbypass.py -i $'..\u200b/' --encode                                                                                                                                                                                   ..%E2%80%8B%2F    

----------------------------------------------
🪪🪪Using zwbypass.py for Emails🪪🪪                                                                                                                                                                                    
📌 Say you want to test if the system lets you sign up with "abc@gmail.com" disguised with zero-width chars.
🌀Insert Zero-Width in Local Part (abc):
./zwbypass.py -i "abc@gmail.com" --mode keywords --keywords abc --zw zwsp  ----> Output "abc@gmail.com" ---> (looks identical, but the local-part "abc" has U+200B inserted). Let me explain and to you more🤹‍♂️❗️         
🌀Run above again but this time we will save it into a file mustafa.txt as shows ----> ./zwbypass.py -i "abc@gmail.com" --mode  keywords --keywords abc --zw zwsp > mustafa.txt                                          
🌀When you saved it to file (mustafa.txt) and inspected:                                                                                                                                                                 
🌀 wc -m mustafa.txt                                                                       
16 mustafa.txt                                                                                                                                                                                                            
🌀Normal abc@gmail.com\n should be 14 characters (12 letters + @ + . + newline). You got 16, which means there are 2 extra invisible characters inside🕵️ ---> ✅ ZWSP inserted                                          
🌀 od -c  mustafa.txt                                                                                                                                                                                                                                                                          
0000000   a 342 200 213   b 342 200 213   c   @   g   m   a   i   l   .
0000020   c   o   m  \n
0000024                                                                                                                                                                                                                                                                                                                                                                                                                                       
🌀a 342 200 213 b 342 200 213 c @ g m a i l . c o m  --> 🌀342 200 213 = UTF-8 encoding of U+200B ZERO WIDTH SPACE --> 🌀Appears after a and b  so the string is actually: a[ZWSP]b[ZWSP]c@gmail.com 🧟‍♀️ So the file does contain invisible ZWSP characters. If you open the file and copy it  the ZWSPs will also be copied (they travel with the text). If you copy directly from terminal output the ZWSPs are also copied, even though you can’t see them. That’s why attackers (and researchers like us) love these characters: they stick around in copy/paste, databases, and forms unless the system strips them. So, whether you copy from terminal or from the file the invisible characters are preserved.                                                                                                                                                                     

🪪🪪So in signup/signin flows🪪🪪                                                                                                                                                                                       
🧟This depends entirely on how the backend handles Unicode: Some systems normalize input (strip zero-widths). Then a​b​c@gmail.com --> abc@gmail.com ---> treated as the same account.                                     
🧟Some systems don’t normalize  they’ll think a​b​c@gmail.com is a different account than abc@gmail.com.                                                                                                                   
🧟Email providers (like Gmail, Outlook) are usually strict  they reject or normalize hidden characters in the local part (before @).                                                                                     
🧟But many custom systems (bug bounty targets, startups, old apps) may not sanitize properly  and that’s where your trick becomes interesting.

---------------------------
🌐With these, you can:                                                                                                                                                  
🔰 Generate bypass payloads (every, random, keywords, homoglyphs).                                                                                                      
🔰 Detect/filter them in captured traffic.                                                                                                                              
🔰 Normalize inputs back to clean form.
