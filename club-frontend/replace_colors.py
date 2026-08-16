import re
import sys

def parse_tag(match):
    # This will match the entire opening tag: e.g. <div className="..." style="...">
    full_tag = match.group(0)
    
    # Extract className
    class_match = re.search(r'className=(["\'])(.*?)\1', full_tag)
    if not class_match:
        return full_tag
        
    classes = class_match.group(2).split(' ')
    quote = class_match.group(1)
    
    new_classes = []
    style_obj = {}
    
    for c in classes:
        if c in ['bg-[#060911]', 'bg-[#090d16]']:
            style_obj['background'] = "'var(--ink)'"
        elif c in ['bg-[#1e293b]', 'bg-[#131c2e]', 'bg-slate-900', 'bg-slate-800']:
            style_obj['background'] = "'var(--surface)'"
        elif c in ['border-[#1e293b]', 'border-[#131c2e]', 'border-slate-700', 'border-slate-800']:
            style_obj['borderColor'] = "'var(--border)'"
        elif c in ['text-slate-400', 'text-gray-400']:
            style_obj['color'] = "'var(--text-dim)'"
        elif c in ['text-[#38bdf8]', 'text-[#8b5cf6]', 'text-[#a78bfa]']:
            style_obj['color'] = "'var(--brand)'"
        elif c in ['bg-[#38bdf8]', 'bg-[#8b5cf6]', 'bg-[#a78bfa]']:
            style_obj['background'] = "'var(--brand)'"
        elif c in ['border-[#38bdf8]', 'border-[#8b5cf6]', 'border-[#a78bfa]', 'border-[#38bdf855]']:
            # The #38bdf855 is #38bdf8 with opacity 55, wait, the rule says replace the cyan accent with brand orange.
            # I will just replace border with brand.
            style_obj['borderColor'] = "'var(--brand)'"
        elif 'from-[#8b5cf6]' in c or 'from-[#38bdf8]' in c:
            new_classes.append(c)
        elif 'to-[#6d28d9]' in c or 'to-[#0284c7]' in c or 'to-[#38bdf8]' in c:
            new_classes.append(c)
        else:
            new_classes.append(c)
            
    # Replace colors inside inline strings if needed, wait, the instructions are for classes.
    if not style_obj:
        return full_tag
        
    # Reconstruct className
    new_class_str = " ".join(new_classes)
    new_class_attr = f'className={quote}{new_class_str}{quote}'
    
    # We might have empty class string, but let's keep it if so.
    if not new_class_str.strip():
        # remove className attr
        full_tag = full_tag.replace(class_match.group(0), '')
    else:
        full_tag = full_tag.replace(class_match.group(0), new_class_attr)
        
    # Find existing style prop
    style_match = re.search(r'style={{(.*?)}}', full_tag)
    if style_match:
        existing_styles = style_match.group(1).strip()
        new_styles = ", ".join([f"{k}: {v}" for k, v in style_obj.items()])
        full_tag = full_tag.replace(style_match.group(0), f'style={{{existing_styles}, {new_styles}}}')
    else:
        new_styles = ", ".join([f"{k}: {v}" for k, v in style_obj.items()])
        # Insert style before the closing bracket of the tag
        # e.g. <div className="..."> -> <div className="..." style={{...}}>
        if full_tag.endswith('/>'):
            full_tag = full_tag[:-2] + f' style={{{new_styles}}} />'
        elif full_tag.endswith('>'):
            full_tag = full_tag[:-1] + f' style={{{new_styles}}}>'
            
    return full_tag

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace the colors in classNames and inject style props
    # We match JSX tags using a regex: <[A-Za-z0-9]+[^>]*className=["'][^"']*["'][^>]*>
    content = re.sub(r'<[A-Za-z0-9]+[^>]*className=["\'][^"\']*["\'][^>]*>', parse_tag, content)
    
    # Also replace raw strings like text-[#38bdf8] -> text-[var(--brand)]
    content = content.replace('bg-[#060911]', 'bg-[var(--ink)]')
    content = content.replace('bg-[#090d16]', 'bg-[var(--ink)]')
    content = content.replace('bg-[#1e293b]', 'bg-[var(--surface)]')
    content = content.replace('bg-[#131c2e]', 'bg-[var(--surface)]')
    content = content.replace('border-[#1e293b]', 'border-[var(--surface)]')
    content = content.replace('text-gray-400', 'text-[var(--text-dim)]')
    content = content.replace('text-slate-400', 'text-[var(--text-dim)]')
    content = content.replace('border-gray-800', 'border-[var(--border)]')
    content = content.replace('border-slate-800', 'border-[var(--border)]')
    content = content.replace('border-slate-700', 'border-[var(--border)]')
    
    # Cyan and Purple accents to Brand
    content = content.replace('#38bdf8', 'var(--brand)')
    content = content.replace('#8b5cf6', 'var(--brand)')
    content = content.replace('#a78bfa', 'var(--brand)')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Processed {filepath}")

files = [
    'c:/Users/jonat/Desktop/dezafira3.0/club-frontend/app/admin/fabrica-biosites/page.tsx',
    'c:/Users/jonat/Desktop/dezafira3.0/club-frontend/app/admin/fabrica-mapas/page.tsx',
    'c:/Users/jonat/Desktop/dezafira3.0/club-frontend/app/admin/fabrica-miniapp/page.tsx'
]

for f in files:
    process_file(f)
