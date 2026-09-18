import re

with open('templates/menu/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Exact match from the actual file - line 42 has different spacing
old = '''<div class="produit-ligne bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col cursor-pointer"
     data-nom="{{ produit.nom|lower }}">'''

# Try with the exact spacing from the file
old2 = '''<div class="produit-ligne bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col cursor-pointer"
     data-nom="{{ produit.nom|lower }}">'''

# Check both
if old in content:
    print("Found version 1")
    content = content.replace(old, old.replace('data-nom="{{ produit.nom|lower }}">', 'data-nom="{{ produit.nom|lower }}" onclick="ajouterAuPanier({{ produit.id }}, \'{{ produit.nom|escapejs }}\', {{ produit.prix }})">'))
elif old2 in content:
    print("Found version 2")
    content = content.replace(old2, old2.replace('data-nom="{{ produit.nom|lower }}">', 'data-nom="{{ produit.nom|lower }}" onclick="ajouterAuPanier({{ produit.id }}, \'{{ produit.nom|escapejs }}\', {{ produit.prix }})">'))
else:
    # Use regex to find and replace the div with more flexibility
    # Look for the pattern and add onclick
    import re
    pattern = r'(<div class="produit-ligne[^"]*cursor-pointer"[^>]*data-nom="\{{\" produit.nom\|lower }}\"[^>]*)>'
    match = re.search(pattern, content)
    if match:
        print("Found via regex")
        original = match.group(1)
        new_original = original + ' onclick="ajouterAuPanier({{ produit.id }}, \'{{ produit.nom|escapejs }}\', {{ produit.prix }})"'
        content = content.replace(original, new_original)
        print("Regex replacement done")
    else:
        print("Could not match with regex either")
        # Just print what we have for debugging
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'produit-ligne' in line.lower() and i < 50:
                print(f'Line {i+1}: {repr(line[:80])}')

with open('templates/menu/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done writing")