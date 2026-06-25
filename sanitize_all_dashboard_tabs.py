import os
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# HELPERS FOR HIGH-FIDELITY OVERWRITING
# ==========================================

def get_sampled_color(img, x, y):
    """Samples the color of a pixel in the image to use as background fill."""
    x = max(0, min(x, img.width - 1))
    y = max(0, min(y, img.height - 1))
    return img.getpixel((x, y))

def get_text_color(bg_color):
    """Determines if text should be light or dark based on background brightness."""
    r, g, b = bg_color[:3]
    brightness = 0.299 * r + 0.587 * g + 0.114 * b
    if brightness > 130:
        return (30, 41, 59, 255) # Dark slate
    else:
        return (249, 250, 251, 255) # Off-white

def draw_sanitized_text(img, draw, font, font_bold, box, text, alignment='left', sample_pos=None, is_bold=False, text_color_override=None):
    """
    Fills the box with a sampled background color and draws the sanitized text on top.
    Looks 100% native.
    """
    x0, y0, x1, y1 = box
    
    # Sample background color
    if sample_pos:
        bg_color = get_sampled_color(img, sample_pos[0], sample_pos[1])
    else:
        bg_color = get_sampled_color(img, x0 - 4, y0 + 4)
        
    # Draw background fill (solid)
    draw.rectangle(box, fill=bg_color)
    
    # Select font
    current_font = font_bold if is_bold else font
    
    # Determine text color
    if text_color_override:
        text_color = text_color_override
    else:
        text_color = get_text_color(bg_color)
        
    # Draw text
    if text:
        try:
            bbox = draw.textbbox((0, 0), text, font=current_font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        except AttributeError:
            w, h = draw.textsize(text, font=current_font) if hasattr(draw, 'textsize') else (80, 14)
            
        bx_w = x1 - x0
        bx_h = y1 - y0
        
        if alignment == 'left':
            tx = x0 + 8
            ty = y0 + (bx_h - h) // 2 - 1
        elif alignment == 'center':
            tx = x0 + (bx_w - w) // 2
            ty = y0 + (bx_h - h) // 2 - 1
        elif alignment == 'right':
            tx = x1 - w - 8
            ty = y0 + (bx_h - h) // 2 - 1
            
        draw.text((tx, ty), text, fill=text_color, font=current_font)

def sanitize_tab_image(input_path, output_path, replacements):
    """Loads a tab screenshot, applies high-fidelity demo data replacements, and saves it."""
    if not os.path.exists(input_path):
        print(f"Warning: {input_path} not found. Skipping.")
        return False
        
    img = Image.open(input_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        font = ImageFont.truetype("segoeui.ttf", 14)
        font_bold = ImageFont.truetype("segoeuib.ttf", 14)
        font_logo = ImageFont.truetype("segoeuib.ttf", 16)
        font_small = ImageFont.truetype("segoeui.ttf", 12)
        font_title = ImageFont.truetype("segoeuib.ttf", 18)
    except IOError:
        try:
            font = ImageFont.truetype("arial.ttf", 13)
            font_bold = ImageFont.truetype("arialbd.ttf", 13)
            font_logo = ImageFont.truetype("arialbd.ttf", 15)
            font_small = ImageFont.truetype("arial.ttf", 11)
            font_title = ImageFont.truetype("arialbd.ttf", 17)
        except IOError:
            font = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            font_logo = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_title = ImageFont.load_default()
            
    for rep in replacements:
        box = rep['box']
        text = rep.get('text', '')
        align = rep.get('align', 'left')
        sample = rep.get('sample', None)
        bold = rep.get('bold', False)
        color_override = rep.get('color', None)
        
        role = rep.get('role', 'body')
        selected_font = font
        selected_bold = font_bold
        
        if role == 'logo':
            selected_font = font_logo
            selected_bold = font_logo
            bold = True
        elif role == 'title':
            selected_font = font_title
            selected_bold = font_title
            bold = True
        elif role == 'small':
            selected_font = font_small
            selected_bold = font_small
            
        draw_sanitized_text(
            img, draw, selected_font, selected_bold, box, text, 
            alignment=align, sample_pos=sample, is_bold=bold, text_color_override=color_override
        )
        
    final_img = img.convert("RGB")
    final_img.save(output_path, "PNG")
    print(f"Sanitized: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    return True

# ==========================================
# REPLACEMENT DEFINITIONS FOR ALL TABS
# ==========================================

def get_standard_header_reps(width):
    """Generates standard header replacements (logo, user email) for the dark navigation bar."""
    return [
        {
            # Cover corporate logo, replace with NL SECURITY
            'box': (15, 10, 200, 50),
            'text': "NL SECURITY",
            'align': 'left',
            'sample': (210, 20),
            'role': 'logo',
            'color': (139, 92, 246, 255) # Glowing violet logo text
        },
        {
            # Cover user email, replace with guest admin
            'box': (width - 300, 10, width - 15, 50),
            'text': "guest_admin@enterprise.com",
            'align': 'right',
            'sample': (width - 320, 20),
            'bold': True
        }
    ]

def main():
    base_dir = r"C:\Users\ny634\Downloads\Port-opening\Final Scripts\Overall-Unused-Automation-4-Steps"
    assets_dir = r"c:\Users\ny634\Downloads\Port-opening\Final Scripts\Github-page\projects\assets"
    
    os.makedirs(assets_dir, exist_ok=True)
    
    # ------------------------------------------
    # 1. LOGIN PAGE (login_page.png: 1600x1000)
    # ------------------------------------------
    login_reps = [
        {
            'box': (20, 20, 400, 75),
            'text': "NEERAJ LAB PORTAL",
            'align': 'left',
            'sample': (410, 30),
            'role': 'logo'
        },
        {
            'box': (600, 435, 980, 475),
            'text': "operator@enterprise.com",
            'align': 'left',
            'sample': (590, 450)
        }
    ]
    sanitize_tab_image(
        os.path.join(base_dir, "login_page.png"),
        os.path.join(assets_dir, "sanitized_login.png"),
        login_reps
    )
    
    # ------------------------------------------
    # 2. OVERVIEW / DASHBOARD (after_login.png: 1600x1000)
    # ------------------------------------------
    overview_reps = get_standard_header_reps(1600)
    # Add overview panel sanitization (e.g. statistics, run logs showing generic counts)
    overview_reps.extend([
        {
            # Overwrite main greeting panel text
            'box': (50, 80, 800, 120),
            'text': "Welcome to the Security Orchestration Dashboard",
            'align': 'left',
            'sample': (40, 100),
            'role': 'title'
        },
        {
            # Overwrite Panorama IP connection status on dashboard
            'box': (100, 200, 500, 240),
            'text': "Connected to Panorama: <PROD_PANORAMA_IP> (Active)",
            'align': 'left',
            'sample': (90, 220),
            'bold': True
        }
    ])
    sanitize_tab_image(
        os.path.join(base_dir, "after_login.png"),
        os.path.join(assets_dir, "sanitized_overview.png"),
        overview_reps
    )
    
    # ------------------------------------------
    # 3. AUDIT TAB (audit tab.png: 1572x1001)
    # ------------------------------------------
    audit_reps = get_standard_header_reps(1572)
    # Table cellular replacements
    row_height = 56
    start_y = 215
    for i in range(13):
        y = start_y + (i * row_height)
        audit_reps.append({
            'box': (60, y, 380, y + 40),
            'text': f"RULE-PROD-SEC-{(i+1):02d}",
            'align': 'left',
            'sample': (50, y + 15)
        })
        audit_reps.append({
            'box': (420, y, 720, y + 40),
            'text': f"owner-{(i+1):02d}@enterprise.com",
            'align': 'left',
            'sample': (410, y + 15)
        })
        audit_reps.append({
            'box': (740, y, 920, y + 40),
            'text': "HQ-SEC-GROUP",
            'align': 'left',
            'sample': (730, y + 15)
        })
    sanitize_tab_image(
        os.path.join(base_dir, "audit tab.png"),
        os.path.join(assets_dir, "sanitized_audit.png"),
        audit_reps
    )
    
    # ------------------------------------------
    # 4. EMAIL NOTIFICATION (email.png: 1635x962)
    # ------------------------------------------
    email_reps = [
        {
            'box': (50, 10, 500, 45),
            'text': "Firewall Review Request - Secure Messaging",
            'align': 'left',
            'sample': (520, 20),
            'bold': True
        },
        {
            'box': (120, 130, 600, 160),
            'text': "security-ops@enterprise.com",
            'align': 'left',
            'sample': (110, 145)
        },
        {
            'box': (120, 170, 600, 200),
            'text': "application-owners@enterprise.com",
            'align': 'left',
            'sample': (110, 185)
        },
        {
            'box': (120, 210, 800, 240),
            'text': "Request for Review - Automated Firewall Hygiene Cleanups",
            'align': 'left',
            'sample': (110, 225),
            'bold': True
        }
    ]
    body_y = 280
    email_paragraphs = [
        "Dear Team,",
        "",
        "As part of the ongoing Firewall Hygiene initiative across the enterprise network,",
        "the Network Security team is reviewing firewall rules that have shown no hits or traffic",
        "within the last 365 days.",
        "",
        "This activity supports cybersecurity compliance and reduces security risk by removing",
        "unused access policies from the production environment.",
        "",
        "Please review your rules and confirm whether any should be excluded using the secure link below:",
        "",
        "https://enterprise.service-now.com/firewall-review?token=SECURE_SSO_KEY_TOKEN",
        "",
        "If a rule is not reviewed or is approved for cleanup, it will be disabled under a change ticket",
        "during the upcoming annual maintenance window.",
        "",
        "Thank you for your support.",
        "",
        "Kind regards,",
        "Network Security Operations Team"
    ]
    for i, para in enumerate(email_paragraphs):
        if para.strip():
            email_reps.append({
                'box': (50, body_y + (i * 24), 1100, body_y + (i * 24) + 22),
                'text': para,
                'align': 'left',
                'sample': (40, body_y + (i * 24) + 10)
            })
    sanitize_tab_image(
        os.path.join(base_dir, "email.png"),
        os.path.join(assets_dir, "sanitized_email.png"),
        email_reps
    )
    
    # ------------------------------------------
    # 5. DISABLE RULES TAB (disable-rules.png: 1583x994)
    # ------------------------------------------
    disable_reps = get_standard_header_reps(1583)
    start_y = 210
    for i in range(12):
        y = start_y + (i * row_height)
        disable_reps.append({
            'box': (60, y, 380, y + 40),
            'text': f"RULE-PROD-SEC-{(i+1):02d}",
            'align': 'left',
            'sample': (50, y + 15)
        })
        disable_reps.append({
            'box': (420, y, 720, y + 40),
            'text': f"owner-{(i+1):02d}@enterprise.com",
            'align': 'left',
            'sample': (410, y + 15)
        })
    sanitize_tab_image(
        os.path.join(base_dir, "disable-rules.png"),
        os.path.join(assets_dir, "sanitized_disable.png"),
        disable_reps
    )
    
    # ------------------------------------------
    # 6. DELETE RULES TAB (delete.png: 1593x987)
    # ------------------------------------------
    delete_reps = get_standard_header_reps(1593)
    start_y = 210
    for i in range(10):
        y = start_y + (i * row_height)
        delete_reps.append({
            'box': (60, y, 380, y + 40),
            'text': f"RULE-PROD-SEC-{(i+1):02d}",
            'align': 'left',
            'sample': (50, y + 15)
        })
        delete_reps.append({
            'box': (420, y, 720, y + 40),
            'text': f"owner-{(i+1):02d}@enterprise.com",
            'align': 'left',
            'sample': (410, y + 15)
        })
    sanitize_tab_image(
        os.path.join(base_dir, "delete.png"),
        os.path.join(assets_dir, "sanitized_delete.png"),
        delete_reps
    )
    
    # ------------------------------------------
    # 7. ADD TAG TAB (tab_addtag.png: 1600x1000)
    # ------------------------------------------
    addtag_reps = get_standard_header_reps(1600)
    start_y = 210
    for i in range(11):
        y = start_y + (i * row_height)
        addtag_reps.append({
            'box': (60, y, 380, y + 40),
            'text': f"RULE-PROD-SEC-{(i+1):02d}",
            'align': 'left',
            'sample': (50, y + 15)
        })
        addtag_reps.append({
            'box': (420, y, 720, y + 40),
            'text': f"owner-{(i+1):02d}@enterprise.com",
            'align': 'left',
            'sample': (410, y + 15)
        })
    sanitize_tab_image(
        os.path.join(base_dir, "tab_addtag.png"),
        os.path.join(assets_dir, "sanitized_addtag.png"),
        addtag_reps
    )
    
    # ------------------------------------------
    # 8. REVIEWS DECISIONS TAB (review decisions.png: 1607x979)
    # ------------------------------------------
    review_decisions_reps = get_standard_header_reps(1607)
    start_y = 210
    for i in range(9):
        y = start_y + (i * row_height)
        review_decisions_reps.append({
            'box': (60, y, 400, y + 40),
            'text': f"RULE-PROD-APP-{(i+1):02d}",
            'align': 'left',
            'sample': (50, y + 15)
        })
        review_decisions_reps.append({
            'box': (420, y, 580, y + 40),
            'text': f"RITM1002{(i+90):02d}",
            'align': 'left',
            'sample': (410, y + 15)
        })
        review_decisions_reps.append({
            'box': (600, y, 880, y + 40),
            'text': "app_owner@enterprise.com",
            'align': 'left',
            'sample': (590, y + 15)
        })
    sanitize_tab_image(
        os.path.join(base_dir, "review decisions.png"),
        os.path.join(assets_dir, "sanitized_review_decisions.png"),
        review_decisions_reps
    )
    
    # ------------------------------------------
    # 9. REVIEWS WORKSPACE TAB (current_reviews.png: 1582x864)
    # ------------------------------------------
    review_reps = [
        {
            'box': (15, 10, 200, 50),
            'text': "NL SECURITY",
            'align': 'left',
            'sample': (210, 20),
            'role': 'logo',
            'color': (139, 92, 246, 255)
        },
        {
            'box': (1300, 10, 1550, 50),
            'text': "app_owner@enterprise.com",
            'align': 'right',
            'sample': (1280, 20),
            'bold': True
        }
    ]
    review_start_y = 190
    review_row_height = 58
    for i in range(8):
        y = review_start_y + (i * review_row_height)
        review_reps.append({
            'box': (60, y, 400, y + 40),
            'text': f"RULE-PROD-APP-{(i+1):02d}",
            'align': 'left',
            'sample': (50, y + 15)
        })
        review_reps.append({
            'box': (420, y, 580, y + 40),
            'text': f"RITM1002{(i+90):02d}",
            'align': 'left',
            'sample': (410, y + 15)
        })
        review_reps.append({
            'box': (600, y, 880, y + 40),
            'text': "app_owner@enterprise.com",
            'align': 'left',
            'sample': (590, y + 15)
        })
    sanitize_tab_image(
        os.path.join(base_dir, "current_reviews.png"),
        os.path.join(assets_dir, "sanitized_review.png"),
        review_reps
    )
    
    # ------------------------------------------
    # 10. JOBS MANAGER (jobs.png: 1635x962)
    # ------------------------------------------
    jobs_reps = get_standard_header_reps(1635)
    log_start_y = 220
    log_line_height = 28
    dummy_logs = [
        "[INFO] 2026-06-25 18:25:01 - Initializing Panorama security rules hit-counter sync...",
        "[INFO] 2026-06-25 18:25:05 - Connecting to primary management server at <PROD_PANORAMA_IP>... [SUCCESS]",
        "[INFO] 2026-06-25 18:25:12 - Loaded 14 active Device Groups from Panorama configuration.",
        "[INFO] 2026-06-25 18:26:04 - Found 284 security policies with zero hit counts in 365 days.",
        "[INFO] 2026-06-25 18:26:08 - Resolving ServiceNow ticket details for identified rule names...",
        "[INFO] 2026-06-25 18:26:45 - ServiceNow REST API resolved owners for 265 rules. 19 rules unresolved.",
        "[INFO] 2026-06-25 18:27:02 - Automatically dispatched consolidated review emails to 42 resolved owners.",
        "[INFO] 2026-06-25 18:27:10 - Logging run details in local SQLite database... [SUCCESS]",
        "[INFO] 2026-06-25 18:27:12 - Job completed successfully. Thread pool workers released.",
        "[INFO] 2026-06-25 18:30:15 - Background thread checking for reviewer submissions...",
        "[INFO] 2026-06-25 18:30:18 - Received 8 decisions from user: app_owner@enterprise.com [UPDATED]"
    ]
    for i, log in enumerate(dummy_logs):
        jobs_reps.append({
            'box': (60, log_start_y + (i * log_line_height), 1300, log_start_y + (i * log_line_height) + 24),
            'text': log,
            'align': 'left',
            'sample': (50, log_start_y + (i * log_line_height) + 12),
            'role': 'small'
        })
    sanitize_tab_image(
        os.path.join(base_dir, "jobs.png"),
        os.path.join(assets_dir, "sanitized_jobs.png"),
        jobs_reps
    )
    
    # ------------------------------------------
    # 11. SETTINGS TAB (settings.png: 1666x944)
    # ------------------------------------------
    settings_reps = get_standard_header_reps(1666)
    settings_reps.extend([
        {
            'box': (450, 185, 900, 220),
            'text': "192.168.1.100",
            'align': 'left',
            'sample': (440, 200)
        },
        {
            'box': (450, 235, 900, 270),
            'text': "192.168.10.150",
            'align': 'left',
            'sample': (440, 250)
        },
        {
            'box': (450, 285, 900, 320),
            'text': "••••••••••••••••••••••••••••••••••••••••",
            'align': 'left',
            'sample': (440, 300)
        },
        {
            'box': (450, 385, 900, 420),
            'text': "smtp.enterprise.com",
            'align': 'left',
            'sample': (440, 400)
        },
        {
            'box': (450, 435, 900, 470),
            'text': "security-ops@enterprise.com",
            'align': 'left',
            'sample': (440, 450)
        },
        {
            'box': (450, 535, 900, 570),
            'text': "https://enterprise.service-now.com",
            'align': 'left',
            'sample': (440, 550)
        },
        {
            'box': (450, 585, 900, 620),
            'text': "svc-account-hygiene",
            'align': 'left',
            'sample': (440, 600)
        },
        {
            'box': (450, 635, 900, 670),
            'text': "••••••••••••••••••••••••",
            'align': 'left',
            'sample': (440, 650)
        }
    ])
    sanitize_tab_image(
        os.path.join(base_dir, "settings.png"),
        os.path.join(assets_dir, "sanitized_settings.png"),
        settings_reps
    )
    
    # ------------------------------------------
    # 12. FLOW CHART (flow.png: 1639x960)
    # ------------------------------------------
    flow_reps = [
        {
            'box': (20, 20, 450, 70),
            'text': "AUTOMATED FIREWALL HYGIENE LIFECYCLE FLOW",
            'align': 'left',
            'sample': (470, 30),
            'role': 'title',
            'color': (139, 92, 246, 255)
        }
    ]
    sanitize_tab_image(
        os.path.join(base_dir, "flow.png"),
        os.path.join(assets_dir, "sanitized_flow.png"),
        flow_reps
    )
    
    print("All dashboard tab screenshots sanitized successfully!")

if __name__ == "__main__":
    main()
