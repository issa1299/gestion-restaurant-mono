import os

# Lire le fichier
with open('templates/menu/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# La ligne à remplacer
old_line = 'let panier = JSON.parse(localStorage.getItem("panier")) || [];'

# La nouvelle ligne avec le correctif
new_lines = '''// Panier client (stocké en localStorage)
let panier = JSON.parse(localStorage.getItem("panier")) || [];
// Au chargement, on s'assure que le panier est propre à zéro
// (évite d'afficher l'ancien panier après un vidage)
if (!localStorage.getItem("panier")) {
    localStorage.setItem("panier", JSON.stringify([]));
}'''

if old_line in content:
    content = content.replace(old_line, new_lines)
    with open('templates/menu/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK - Fix appliqué : templates/menu/index.html")
else:
    print("Pattern non trouvé")