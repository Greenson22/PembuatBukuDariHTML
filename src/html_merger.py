import os
from pathlib import Path
from bs4 import BeautifulSoup

def generate_combined_html(files, options, progress_callback=None):
    if not files:
        return None

    doc_title = options.get("doc_title", "Gabungan Materi")
    is_pdf = options.get("is_pdf", False)
    use_toc = options.get("use_toc", True)

    # --- 1. HEAD & CSS ---
    html_head = "\n<!DOCTYPE html>\n<html lang='id'>\n<head>\n"
    html_head += "    <meta charset='UTF-8'>\n"
    html_head += f"    <title>{doc_title}</title>\n"
    html_head += "    <style>\n"
    html_head += "        body { font-family: Arial, sans-serif; line-height: 1.6; }\n"
    html_head += "        .section-container { margin-bottom: 50px; padding-bottom: 20px; }\n"
    html_head += "        .page-break { page-break-before: always; }\n"
    
    if use_toc:
        html_head += """
            .toc-container { margin-bottom: 50px; }
            .toc-container h1 { text-align: center; margin-bottom: 30px; }
            .toc-list { list-style-type: none; padding: 0; }
            .toc-list li { margin-bottom: 10px; font-size: 14pt; }
            .toc-list a { text-decoration: none; color: #333; display: block; }
        """
        if is_pdf:
            html_head += ".toc-list a.toc-link::after { content: leader('.') target-counter(attr(href), page); }"

    if is_pdf:
        page_size = options.get("page_size", "A4")
        m_top, m_bottom, m_left, m_right = options.get("margins", (25, 25, 25, 25))

        html_head += f"""
            @page {{
                size: {page_size};
                margin: {m_top}mm {m_right}mm {m_bottom}mm {m_left}mm;
        """
        
        author_text = options.get("author_text", "")
        hf_pos = options.get("hf_pos", "Header")
        hf_align = options.get("hf_align", "Kiri")
        use_page_numbers = options.get("use_page_numbers", True)

        if author_text:
            pos = "top" if hf_pos == "Header" else "bottom"
            align = "left"
            if hf_align == "Tengah": align = "center"
            elif hf_align == "Kanan": align = "right"
            
            if use_page_numbers and pos == "bottom" and align == "right":
                html_head += f"""
                    @bottom-right {{ content: "{author_text} | Halaman " counter(page) " dari " counter(pages); font-family: Arial, sans-serif; font-size: 10pt; color: #555; }}
                """
            else:
                html_head += f"""
                    @{pos}-{align} {{ content: "{author_text}"; font-family: Arial, sans-serif; font-size: 10pt; color: #555; }}
                """
                if use_page_numbers:
                    html_head += """
                        @bottom-right { content: "Halaman " counter(page) " dari " counter(pages); font-family: Arial, sans-serif; font-size: 10pt; color: #555; }
                    """
        else:
            if use_page_numbers:
                html_head += """
                    @bottom-right { content: "Halaman " counter(page) " dari " counter(pages); font-family: Arial, sans-serif; font-size: 10pt; color: #555; }
                """

        html_head += "        }\n"

        # --- TERAPKAN LATAR BELAKANG HALAMAN COVER ---
        cover_bg_color = options.get("cover_bg_color", "#ffffff")
        html_head += f"""
        @page cover {{
            background-color: {cover_bg_color};
        """
        # Sembunyikan header dan footer pada sampul
        if use_page_numbers or author_text:
            html_head += """
            @top-left { content: none; }
            @top-center { content: none; }
            @top-right { content: none; }
            @bottom-left { content: none; }
            @bottom-center { content: none; }
            @bottom-right { content: none; }
            """
        html_head += """
        }
        .cover-container { page: cover; }
        """

    else:
        cover_bg_color = options.get("cover_bg_color", "#ffffff")
        html_head += f"        .cover-container {{ background-color: {cover_bg_color}; }}\n"

    html_head += "    </style>\n</head>\n<body>\n"

    # --- 2. COVER ---
    cover_html = ""
    cover_type = options.get("cover_type", "none")
    if cover_type == "html" and options.get("cover_file_path"):
        with open(options["cover_file_path"], 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            body_content = soup.find('body')
            content = str(body_content.decode_contents()) if body_content else str(soup)
            cover_html += f"    <div class='cover-container'>\n{content}\n    </div>\n"
            if is_pdf: cover_html += "    <div class='page-break'></div>\n"
    elif cover_type == "image" and options.get("cover_image_path"):
        file_uri = Path(os.path.abspath(options["cover_image_path"])).as_uri()
        # Menerapkan object-fit: contain agar gambar tidak terpotong dan membiarkan ruang sisa mengikuti warna backgroud (terhubung ke warna ujung piksel)
        cover_html += f"<div class='cover-container' style='width: 100%; height: 98vh; overflow: hidden; display: flex; align-items: center; justify-content: center;'><img src='{file_uri}' style='width: 100%; height: 100%; object-fit: contain; display: block;' /></div>\n"
        if is_pdf: cover_html += "    <div class='page-break'></div>\n"
    elif cover_type == "text":
        judul = doc_title if doc_title else "Judul Dokumen (Kosong)"
        cover_html += f"<div class='cover-container' style='text-align: center; margin-top: 35%; padding: 20px;'><h1 style='font-size: 42pt; color: #2c3e50;'>{judul}</h1></div>\n"
        if is_pdf: cover_html += "    <div class='page-break'></div>\n"

    # --- 3. DAFTAR ISI KEPALA ---
    toc_html = ""
    if use_toc:
        toc_html += "<div class='toc-container'>\n    <h1>Daftar Isi</h1>\n    <ul class='toc-list'>\n"

    # --- 4. RENDER ISI & STYLING ---
    body_html = ""
    current_bab = None
    is_first_body_item = True 
    
    bab_style_mode = options.get("bab_style_mode", "Klasik Tengah (Default)")
    bab_font_size = options.get("bab_font_size", 16)
    materi_font_size = options.get("materi_font_size", 12)
    materi_style_text = options.get("materi_style_text", "Normal")
    
    m_font_style = "italic" if "Miring" in materi_style_text else "normal"
    m_font_weight = "bold" if "Tebal" in materi_style_text else "normal"

    custom_titles = options.get("custom_titles", {})
    file_bab_mapping = options.get("file_bab_mapping", {})

    for i, file_path in enumerate(files):
        file_name = os.path.basename(file_path)
        display_title = custom_titles.get(file_name, file_name.replace('.html', '').replace('_', ' ').replace('-', ' ').title())
        bab_title = file_bab_mapping.get(file_name)
        
        if bab_title and bab_title != current_bab:
            current_bab = bab_title
            bab_id = f"bab-{i}"
            
            if use_toc:
                toc_html += f"        <li style='margin-top: 20px; font-weight: bold; font-size: 16pt;'><a href='#{bab_id}' class='toc-link'>{bab_title}</a></li>\n"
            
            if is_pdf and not is_first_body_item:
                body_html += "    <div class='page-break'></div>\n"
            
            if "Modern Kiri" in bab_style_mode:
                body_html += f"""
                <div class='bab-container' id='{bab_id}' style='margin-top: 15%; margin-bottom: 50px; text-align: left; border-bottom: 4px solid #2980b9; padding-bottom: 15px;'>
                    <h1 style='font-size: {bab_font_size}pt; color: #2c3e50; margin: 0;'>{bab_title}</h1>
                </div>
                """
            elif "Blok Latar Warna" in bab_style_mode:
                body_html += f"""
                <div class='bab-container' id='{bab_id}' style='margin-top: 25%; margin-bottom: 50px; text-align: center; background-color: #ecf0f1; padding: 40px 20px; border-radius: 8px; border-left: 10px solid #34495e;'>
                    <h1 style='font-size: {bab_font_size}pt; color: #2c3e50; margin: 0;'>{bab_title}</h1>
                </div>
                """
            elif "Minimalis Elegan" in bab_style_mode:
                body_html += f"""
                <div class='bab-container' id='{bab_id}' style='margin-top: 30%; margin-bottom: 50px; text-align: center;'>
                    <h1 style='font-size: {bab_font_size}pt; color: #333; font-weight: normal; letter-spacing: 5px; text-transform: uppercase; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 25px 0;'>{bab_title}</h1>
                </div>
                """
            else: 
                body_html += f"""
                <div class='bab-container' id='{bab_id}' style='text-align: center; margin-top: 30%; margin-bottom: 50px;'>
                    <h1 style='font-size: {bab_font_size}pt; color: #000; margin: 0;'>{bab_title}</h1>
                </div>
                """
            
            is_first_body_item = False
            if is_pdf:
                body_html += "    <div class='page-break'></div>\n"
        else:
            if is_pdf and not is_first_body_item:
                body_html += "    <div class='page-break'></div>\n"

        element_id = f"file-{i}" 
        if use_toc:
            margin_kiri = "margin-left: 20px;" if current_bab else ""
            toc_html += f"        <li style='{margin_kiri}'><a href='#{element_id}' class='toc-link'>Materi: {display_title}</a></li>\n"

        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            body_content = soup.find('body')
            content = str(body_content.decode_contents()) if body_content else str(soup)
            
            body_html += f"    <div class='section-container' id='{element_id}'>\n"
            body_html += f"        <div style='font-size: {materi_font_size}pt; font-style: {m_font_style}; font-weight: {m_font_weight}; color: #555; margin-bottom: 15px;'>{display_title}</div>\n"
            body_html += content
            body_html += "\n    </div>\n"
        
        is_first_body_item = False 
        if progress_callback:
            progress_callback(i + 1)

    if use_toc:
        toc_html += "    </ul>\n</div>\n"
        if is_pdf:
            toc_html += "<div class='page-break'></div>\n"

    return html_head + cover_html + toc_html + body_html + "</body>\n</html>"