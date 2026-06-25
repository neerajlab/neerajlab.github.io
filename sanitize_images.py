import os
from PIL import Image, ImageDraw, ImageFont

def sanitize_image(input_path, output_path, steps):
    """
    Loads an image, draws professional masking/redaction overlays, and saves it.
    steps is a list of dicts: {'box': (x0, y0, x1, y1), 'label': 'Text', 'color': (r,g,b)}
    """
    if not os.path.exists(input_path):
        print(f"Warning: {input_path} not found. Skipping.")
        return False
        
    img = Image.open(input_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # Try to load a default font
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        font_bold = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        
    for step in steps:
        box = step['box']
        label = step.get('label', '')
        color = step.get('color', (30, 41, 59, 230)) # Dark slate default
        border_color = step.get('border_color', (139, 92, 246, 255)) # Violet accent border
        
        # Draw solid/semi-transparent background rectangle
        draw.rectangle(box, fill=color, outline=border_color, width=1)
        
        # Draw label text if provided
        if label:
            # Calculate text size using textbbox
            try:
                bbox = draw.textbbox((0, 0), label, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
            except AttributeError:
                # Fallback for older PIL versions
                w, h = draw.textsize(label, font=font) if hasattr(draw, 'textsize') else (100, 15)
                
            # Center text in box
            bx_w = box[2] - box[0]
            bx_h = box[3] - box[1]
            tx = box[0] + (bx_w - w) // 2
            ty = box[1] + (bx_h - h) // 2
            
            # Draw text shadow
            draw.text((tx + 1, ty + 1), label, fill=(0, 0, 0, 150), font=font)
            # Draw text
            draw.text((tx, ty), label, fill=(249, 250, 251, 255), font=font)
            
    # Convert back to RGB and save
    final_img = img.convert("RGB")
    final_img.save(output_path, "PNG")
    print(f"Saved sanitized image: {output_path}")
    return True

def main():
    base_dir = r"C:\Users\ny634\Downloads\Port-opening\Final Scripts\Overall-Unused-Automation-4-Steps"
    assets_dir = r"c:\Users\ny634\Downloads\Port-opening\Final Scripts\Github-page\projects\assets"
    
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Sanitize Login Page (login_page.png: 1600x1000)
    # Mask corporate brand logos or any hardcoded internal texts
    login_steps = [
        {
            # Cover Top-Left Logo/Brand
            'box': (10, 10, 320, 70),
            'label': 'SECURE GATEWAY // ENTERPRISE',
            'color': (15, 23, 42, 255),
            'border_color': (6, 182, 212, 255)
        },
        {
            # Cover username input field if it has pre-filled value
            'box': (600, 430, 1000, 480),
            'label': 'username@enterprise.com',
            'color': (30, 41, 59, 255),
            'border_color': (139, 92, 246, 255)
        }
    ]
    sanitize_image(
        os.path.join(base_dir, "login_page.png"),
        os.path.join(assets_dir, "sanitized_login.png"),
        login_steps
    )
    
    # 2. Sanitize Audit Tab (audit tab.png: 1572x1001)
    # Cover the top bar (which has corporate logo and user WWID)
    # Mask the table columns containing actual rules, device groups, and emails
    audit_steps = [
        {
            # Cover Top Header Corporate branding
            'box': (0, 0, 1572, 60),
            'label': 'SECURITY ORCHESTRATION & HYGIENE PORTAL  |  SESSION: SECURE',
            'color': (15, 23, 42, 255),
            'border_color': (139, 92, 246, 255)
        },
        {
            # Mask the rule name column data to protect internal naming conventions
            'box': (50, 180, 400, 950),
            'label': '[ SECURITY RULES MASKED FOR PRIVACY ]',
            'color': (17, 24, 39, 240),
            'border_color': (6, 182, 212, 100)
        },
        {
            # Mask emails and WWIDs in the table
            'box': (410, 180, 750, 950),
            'label': 'owner-address@enterprise.com',
            'color': (17, 24, 39, 240),
            'border_color': (6, 182, 212, 100)
        }
    ]
    sanitize_image(
        os.path.join(base_dir, "audit tab.png"),
        os.path.join(assets_dir, "sanitized_audit.png"),
        audit_steps
    )
    
    # 3. Sanitize Email (email.png: 1635x962)
    # Mask the To, From, CC headers and the body text containing Cummins/WWID
    email_steps = [
        {
            # Cover Outlook/Webmail Header
            'box': (0, 0, 1635, 120),
            'label': 'SECURE MAIL DELIVERY // ENCRYPTED TRANSIT',
            'color': (15, 23, 42, 255),
            'border_color': (139, 92, 246, 255)
        },
        {
            # Mask Email Recipients & Metadata
            'box': (20, 130, 800, 240),
            'label': 'From: security-ops@enterprise.com | To: application-owners@enterprise.com',
            'color': (30, 41, 59, 255),
            'border_color': (6, 182, 212, 255)
        },
        {
            # Mask Email Body referencing Cummins/Internal details
            'box': (20, 260, 1615, 940),
            'label': 'Dear Team,\n\nAs part of the ongoing Firewall Hygiene initiative across the Enterprise firewall environment,\nthe Network Security team is reviewing firewall rules that have shown no hits or traffic within the last 365 days.\n\nPlease review your rules using the secure link below to submit your decisions (Exclude, Retain, Disable, Delete):\n\nhttps://enterprise.service-now.com/firewall-review?token=<SECURE_TOKEN>\n\nKind regards,\nNetwork Security Operations',
            'color': (17, 24, 39, 255),
            'border_color': (139, 92, 246, 150)
        }
    ]
    sanitize_image(
        os.path.join(base_dir, "email.png"),
        os.path.join(assets_dir, "sanitized_email.png"),
        email_steps
    )
    
    # 4. Sanitize Review Link Portal (current_reviews.png: 1582x864)
    # Mask the header and the rule/ticket details
    review_steps = [
        {
            # Cover Top Header
            'box': (0, 0, 1582, 60),
            'label': 'SECURE PORTAL: INDIVIDUAL DECISION SPACE  |  USER: authenticated_owner',
            'color': (15, 23, 42, 255),
            'border_color': (139, 92, 246, 255)
        },
        {
            # Mask rules list
            'box': (40, 150, 600, 820),
            'label': '[ CONSOLIDATED RULE LIST MASKED ]',
            'color': (17, 24, 39, 240),
            'border_color': (6, 182, 212, 100)
        },
        {
            # Mask ticket numbers and emails
            'box': (610, 150, 1100, 820),
            'label': 'Ticket: RITM<RESOLVED_TICKET_ID> | Owner: owner@enterprise.com',
            'color': (17, 24, 39, 240),
            'border_color': (6, 182, 212, 100)
        }
    ]
    sanitize_image(
        os.path.join(base_dir, "current_reviews.png"),
        os.path.join(assets_dir, "sanitized_review.png"),
        review_steps
    )
    
    # 5. Sanitize Jobs/Execution Portal (jobs.png: 1635x962)
    # Mask background jobs and execution details
    jobs_steps = [
        {
            # Cover Top Header
            'box': (0, 0, 1635, 60),
            'label': 'SECURITY ORCHESTRATION & HYGIENE PORTAL  |  JOB SCHEDULER & PIPELINE',
            'color': (15, 23, 42, 255),
            'border_color': (139, 92, 246, 255)
        },
        {
            # Mask Job Execution Details
            'box': (50, 180, 1580, 930),
            'label': '[ BACKGROUND EXECUTION AND PANORAMA SYNC LOGS MASKED FOR PRIVACY ]\n\nJob Status: RUNNING | Threads: Concurrent parallel execution actively processing Panorama commands.',
            'color': (17, 24, 39, 245),
            'border_color': (6, 182, 212, 100)
        }
    ]
    sanitize_image(
        os.path.join(base_dir, "jobs.png"),
        os.path.join(assets_dir, "sanitized_jobs.png"),
        jobs_steps
    )
    
    # 6. Sanitize Flow (flow.png: 1639x960)
    flow_steps = [
        {
            'box': (0, 0, 1639, 60),
            'label': 'AUTOMATED ORCHESTRATION FLOW CHART',
            'color': (15, 23, 42, 255),
            'border_color': (139, 92, 246, 255)
        }
    ]
    sanitize_image(
        os.path.join(base_dir, "flow.png"),
        os.path.join(assets_dir, "sanitized_flow.png"),
        flow_steps
    )
    
    print("Image sanitization complete!")

if __name__ == "__main__":
    main()
