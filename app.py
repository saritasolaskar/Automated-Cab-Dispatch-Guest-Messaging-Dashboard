import streamlit as st
import pandas as pd
import urllib.parse
import re
import hashlib
from datetime import datetime, time
import streamlit.components.v1 as components

st.set_page_config(page_title="Cab Dispatch Control Center", layout="wide", page_icon="🚗")

# ----------------------------------------------------
# 1. STYLES & SESSION STATE INITIALIZATION
# ----------------------------------------------------
st.markdown("""
<style>
    .badge-ready { background-color: #28a745; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; }
    .badge-new { background-color: #007bff; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; }
    .badge-incomplete { background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; }
    .badge-sent { background-color: #6c757d; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; }
    .card-box { border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

if 'sent_records' not in st.session_state:
    st.session_state['sent_records'] = set()

if 'previous_hashes' not in st.session_state:
    st.session_state['previous_hashes'] = {}

# ----------------------------------------------------
# 2. EVENT CONTROLS
# ----------------------------------------------------
st.title("🚗 Cab Dispatch & Guest Messaging System")
st.caption("Upload allocation sheets, track sent status, identify incomplete records, and copy/send messages in 1 click.")

col_date, col_drop = st.columns([1, 2])
with col_date:
    event_date = st.text_input("📅 Reporting Date", value="22/08/2026")
with col_drop:
    drop_address = st.text_input("🏨 Destination Drop Location", value="Rakabi the Fern Igatpuri Series by Marriott")

uploaded_file = st.file_uploader("📂 Upload Cab Allocation Excel File (.xlsx)", type=["xlsx", "xls"])

# ----------------------------------------------------
# 3. HELPER FUNCTIONS & CLEANERS
# ----------------------------------------------------
def clean_phone(phone):
    if pd.isna(phone):
        return ""
    raw = str(phone).replace(".0", "").strip()
    parts = re.split(r'[/,;]', raw)
    cleaned = []
    for p in parts:
        digits = re.sub(r'\D', '', p.strip())
        if len(digits) == 10:
            cleaned.append(digits)
        elif len(digits) > 10 and digits.startswith("91") and len(digits) == 12:
            cleaned.append(digits[2:])
        elif digits:
            cleaned.append(digits)
    return " / ".join(cleaned)

def clean_cab_type(cab_type):
    if pd.isna(cab_type):
        return "Sedan/SUV"
    c = str(cab_type).strip()
    if "desire" in c.lower() or "dzire" in c.lower():
        return "Dzire"
    elif "ertiga" in c.lower():
        return "Ertiga"
    elif "innova" in c.lower():
        return "Innova"
    return c

def format_pickup_time(time_val):
    if pd.isna(time_val) or not str(time_val).strip():
        return ""
    if isinstance(time_val, (time, datetime)):
        return time_val.strftime("%I:%M %p").lstrip("0")
    t_str = str(time_val).strip().upper().replace("A.M.", "AM").replace("P.M.", "PM").replace(".", ":")
    return re.sub(r'\s+', ' ', t_str)

def compute_record_hash(row):
    """Creates a unique signature of the row content to detect updates."""
    key_data = f"{row.get('Dr. Name')}_{row.get('Driver Name')}_{row.get('Vehicle NO')}_{row.get('Driver NO')}_{row.get('Pick Up')}"
    return hashlib.md5(key_data.encode('utf-8')).hexdigest()

def render_copy_button(text_to_copy, button_id):
    """Renders a 1-click clipboard copy button."""
    escaped_text = text_to_copy.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\n", "\\n")
    html_code = f"""
    <button id="btn_{button_id}" onclick="copyText_{button_id}()" 
        style="width: 100%; padding: 8px; background-color: #f0f2f6; border: 1px solid #d0d4dc; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px;">
        📋 Copy Text
    </button>
    <script>
    function copyText_{button_id}() {{
        navigator.clipboard.writeText(`{escaped_text}`);
        var btn = document.getElementById("btn_{button_id}");
        btn.innerText = "✅ Copied!";
        btn.style.backgroundColor = "#d4edda";
        btn.style.borderColor = "#c3e6cb";
        setTimeout(() => {{
            btn.innerText = "📋 Copy Text";
            btn.style.backgroundColor = "#f0f2f6";
            btn.style.borderColor = "#d0d4dc";
        }}, 2000);
    }}
    </script>
    """
    components.html(html_code, height=45)

def build_message(row, reporting_date, drop_addr):
    passenger_name = str(row.get('Dr. Name', '')).strip()
    passenger_no = clean_phone(row.get('Contact No.', ''))
    driver_name = str(row.get('Driver Name', '')).strip()
    driver_no = clean_phone(row.get('Driver NO', ''))
    vehicle_no = str(row.get('Vehicle NO', '')).strip()
    cab_type = clean_cab_type(row.get('Cab Type', ''))
    pickup_time = format_pickup_time(row.get('Pick Up', ''))
    reporting_address = str(row.get('Address', '')).strip()

    missing_fields = []
    if not driver_name or driver_name.lower() == 'nan': missing_fields.append("Driver Name")
    if not driver_no: missing_fields.append("Driver Number")
    if not vehicle_no or vehicle_no.lower() == 'nan': missing_fields.append("Vehicle Number")
    if not passenger_no: missing_fields.append("Passenger Number")
    if not pickup_time: missing_fields.append("Pickup Time")

    msg = (
        f"Vehicle and driver details for\n"
        f"Passenger: {passenger_name}\n"
        f"Number :- {passenger_no}\n\n"
        f"Driver: {driver_name if driver_name else 'TBD'}\n"
        f"Number: {driver_no if driver_no else 'TBD'}\n"
        f"Vehicle: {vehicle_no if vehicle_no else 'TBD'}\n"
        f"Vehicle : {cab_type}\n"
        f"Reporting on {reporting_date} at {pickup_time if pickup_time else 'TBD'}\n\n"
        f"Reporting address :- {reporting_address}\n"
        f"Drop Address :-{drop_addr}"
    )
    return msg, missing_fields

# ----------------------------------------------------
# 4. EXCEL DATA INGESTION
# ----------------------------------------------------
def load_excel_smart(file, sheet_name):
    raw_df = pd.read_excel(file, sheet_name=sheet_name, header=None)
    header_idx = 0
    for idx, row in raw_df.iterrows():
        row_vals = [str(v).lower().strip() for v in row.values if pd.notna(v)]
        if any("sr" in v or "dr. name" in v or "driver" in v or "passenger" in v for v in row_vals):
            header_idx = idx
            break
    df = pd.read_excel(file, sheet_name=sheet_name, header=header_idx)
    df.columns = [str(c).strip() for c in df.columns]
    return df

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names
    default_idx = 1 if len(sheets) > 1 else 0
    selected_sheet = st.selectbox("📄 Select Sheet", sheets, index=default_idx)
    
    df = load_excel_smart(uploaded_file, selected_sheet)
    
    # Process & analyze each row
    processed_items = []
    
    for idx, row in df.iterrows():
        passenger = str(row.get('Dr. Name', '')).strip()
        if not passenger or passenger.lower() in ['nan', 'dr. name']:
            continue
            
        sr_no = str(row.get('SR No.', idx + 1)).replace('.0', '').strip()
        record_id = f"ROUTE_{sr_no}_{passenger}"
        current_hash = compute_record_hash(row)
        
        msg, missing_fields = build_message(row, event_date, drop_address)
        
        # Determine status tag
        is_sent = record_id in st.session_state['sent_records']
        is_incomplete = len(missing_fields) > 0
        
        # Check if record is new or modified since last upload
        is_new_or_updated = False
        if record_id in st.session_state['previous_hashes']:
            if st.session_state['previous_hashes'][record_id] != current_hash:
                is_new_or_updated = True
        elif st.session_state['previous_hashes']: # If previous uploads existed and this is a new route
            is_new_or_updated = True
            
        # Update hash in session
        st.session_state['previous_hashes'][record_id] = current_hash
        
        if is_sent:
            tag = "SENT"
        elif is_incomplete:
            tag = "INCOMPLETE"
        elif is_new_or_updated:
            tag = "NEW / UPDATED"
        else:
            tag = "READY"
            
        processed_items.append({
            'record_id': record_id,
            'sr_no': sr_no,
            'passenger': passenger,
            'msg': msg,
            'missing': missing_fields,
            'tag': tag,
            'is_sent': is_sent,
            'row_idx': idx
        })
        
    # ----------------------------------------------------
    # 5. METRICS & FILTER BAR
    # ----------------------------------------------------
    total_count = len(processed_items)
    ready_count = sum(1 for x in processed_items if x['tag'] == 'READY')
    new_count = sum(1 for x in processed_items if x['tag'] == 'NEW / UPDATED')
    incomplete_count = sum(1 for x in processed_items if x['tag'] == 'INCOMPLETE')
    sent_count = sum(1 for x in processed_items if x['tag'] == 'SENT')

    st.markdown("---")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Passengers", total_count)
    m2.metric("🟢 Ready to Send", ready_count)
    m3.metric("🆕 New / Updated", new_count)
    m4.metric("⚠️ Incomplete", incomplete_count)
    m5.metric("✅ Already Sent", sent_count)

    # Filter Tabs
    filter_choice = st.radio(
        "🔍 Filter View:",
        ["All Messages", "🟢 Ready to Send", "🆕 New / Updated", "⚠️ Incomplete", "⏳ Unsent Only", "✅ Sent"],
        horizontal=True
    )
    
    # Filter items based on user choice
    display_items = []
    for item in processed_items:
        if filter_choice == "All Messages":
            display_items.append(item)
        elif filter_choice == "🟢 Ready to Send" and item['tag'] == 'READY':
            display_items.append(item)
        elif filter_choice == "🆕 New / Updated" and item['tag'] == 'NEW / UPDATED':
            display_items.append(item)
        elif filter_choice == "⚠️ Incomplete" and item['tag'] == 'INCOMPLETE':
            display_items.append(item)
        elif filter_choice == "⏳ Unsent Only" and item['tag'] != 'SENT':
            display_items.append(item)
        elif filter_choice == "✅ Sent" and item['tag'] == 'SENT':
            display_items.append(item)

    st.markdown(f"**Showing {len(display_items)} message(s)**")

    # ----------------------------------------------------
    # 6. RENDER MESSAGE CARDS
    # ----------------------------------------------------
    cols = st.columns(2)
    for i, item in enumerate(display_items):
        encoded_msg = urllib.parse.quote(item['msg'])
        whatsapp_url = f"https://api.whatsapp.com/send?text={encoded_msg}"
        rec_id = item['record_id']

        # Tag Badges HTML
        if item['tag'] == 'READY':
            tag_html = '<span class="badge-ready">🟢 READY TO SEND</span>'
        elif item['tag'] == 'NEW / UPDATED':
            tag_html = '<span class="badge-new">🆕 NEW / UPDATED</span>'
        elif item['tag'] == 'INCOMPLETE':
            tag_html = '<span class="badge-incomplete">⚠️ INCOMPLETE</span>'
        else:
            tag_html = '<span class="badge-sent">✅ SENT</span>'

        with cols[i % 2]:
            with st.container(border=True):
                # Header row with Route No and Tag
                c_title, c_badge = st.columns([3, 2])
                with c_title:
                    st.markdown(f"### Route #{item['sr_no']} — {item['passenger']}")
                with c_badge:
                    st.markdown(f"<div style='text-align:right;'>{tag_html}</div>", unsafe_allow_html=True)

                if item['missing']:
                    st.error(f"Missing details: **{', '.join(item['missing'])}**")

                # Message display
                st.code(item['msg'], language="text")

                # Actions row: Copy Button | WhatsApp Button | Mark as Sent Checkbox
                btn_col1, btn_col2, btn_col3 = st.columns([1.2, 1.4, 1.4])
                
                with btn_col1:
                    render_copy_button(item['msg'], f"btn_{item['row_idx']}")
                    
                with btn_col2:
                    st.link_button("📲 Send WhatsApp", whatsapp_url, use_container_width=True)
                    
                with btn_col3:
                    is_checked = item['is_sent']
                    if st.checkbox("Mark Sent", value=is_checked, key=f"chk_{rec_id}"):
                        st.session_state['sent_records'].add(rec_id)
                    else:
                        st.session_state['sent_records'].discard(rec_id)

    # ----------------------------------------------------
    # 7. SIDEBAR BATCH OPERATIONS
    # ----------------------------------------------------
    st.sidebar.markdown("### ⚡ Batch Controls")
    
    col_s1, col_s2 = st.sidebar.columns(2)
    with col_s1:
        if st.button("Mark All Sent", use_container_width=True):
            for itm in processed_items:
                st.session_state['sent_records'].add(itm['record_id'])
            st.rerun()
    with col_s2:
        if st.button("Reset Sent", use_container_width=True):
            st.session_state['sent_records'].clear()
            st.rerun()

    st.sidebar.markdown("---")
    
    # Download Unsent Only
    unsent_msgs = [it['msg'] for it in processed_items if it['record_id'] not in st.session_state['sent_records']]
    if unsent_msgs:
        unsent_text = "\n\n" + ("\n" + "="*45 + "\n\n").join(unsent_msgs)
        st.sidebar.download_button(
            label=f"📥 Download Unsent ({len(unsent_msgs)})",
            data=unsent_text,
            file_name="Unsent_Cab_Messages.txt",
            mime="text/plain",
            use_container_width=True
        )

    # Download All
    all_msgs = [it['msg'] for it in processed_items]
    if all_msgs:
        all_text = "\n\n" + ("\n" + "="*45 + "\n\n").join(all_msgs)
        st.sidebar.download_button(
            label="📥 Download All Messages (.txt)",
            data=all_text,
            file_name="All_Cab_Messages.txt",
            mime="text/plain",
            use_container_width=True
        )