{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
import matplotlib.pyplot as plt\
import os\
import tempfile\
from data_processor import SaunaDataProcessor\
\
# \uc0\u12479 \u12452 \u12488 \u12523 \u12392 \u12452 \u12531 \u12488 \u12525 \u12480 \u12463 \u12471 \u12519 \u12531 \
st.title('\uc0\u12469 \u12454 \u12490 \u26045 \u35373 \u12487 \u12540 \u12479 \u20998 \u26512 \u12480 \u12483 \u12471 \u12517 \u12508 \u12540 \u12489 ')\
st.write('CSV\uc0\u12501 \u12449 \u12452 \u12523 \u12434 \u12450 \u12483 \u12503 \u12525 \u12540 \u12489 \u12375 \u12390 \u12289 \u12469 \u12454 \u12490 \u26045 \u35373 \u12398 \u12487 \u12540 \u12479 \u12434 \u20998 \u26512 \u12375 \u12414 \u12377 \u12290 ')\
\
# \uc0\u12501 \u12449 \u12452 \u12523 \u12450 \u12483 \u12503 \u12525 \u12540 \u12489 \u37096 \u20998 \
st.header('\uc0\u12487 \u12540 \u12479 \u12501 \u12449 \u12452 \u12523 \u12398 \u12450 \u12483 \u12503 \u12525 \u12540 \u12489 ')\
uploaded_files = st.file_uploader('CSV\uc0\u12501 \u12449 \u12452 \u12523 \u12434 \u12450 \u12483 \u12503 \u12525 \u12540 \u12489 \u12375 \u12390 \u12367 \u12384 \u12373 \u12356 ', \
                               type=['csv'], accept_multiple_files=True)\
\
if uploaded_files:\
    # \uc0\u19968 \u26178 \u12487 \u12451 \u12524 \u12463 \u12488 \u12522 \u12434 \u20316 \u25104 \u12375 \u12390 \u12501 \u12449 \u12452 \u12523 \u12434 \u20445 \u23384 \
    temp_dir = tempfile.mkdtemp()\
    file_paths = \{\}\
    \
    for uploaded_file in uploaded_files:\
        file_path = os.path.join(temp_dir, uploaded_file.name)\
        with open(file_path, 'wb') as f:\
            f.write(uploaded_file.getbuffer())\
        file_paths[uploaded_file.name] = file_path\
    \
    st.success(f'\{len(uploaded_files)\}\uc0\u20491 \u12398 \u12501 \u12449 \u12452 \u12523 \u12364 \u12450 \u12483 \u12503 \u12525 \u12540 \u12489 \u12373 \u12428 \u12414 \u12375 \u12383 ')\
    \
    # \uc0\u12501 \u12449 \u12452 \u12523 \u12434 \u20998 \u39006 \
    member_files = [f for f in file_paths.keys() if 'member' in f.lower()]\
    reservation_files = [f for f in file_paths.keys() if 'reservation' in f.lower()]\
    frame_files = [f for f in file_paths.keys() if 'frame' in f.lower()]\
    sales_files = [f for f in file_paths.keys() if 'sales' in f.lower()]\
    \
    # \uc0\u12503 \u12525 \u12475 \u12483 \u12469 \u12540 \u12434 \u21021 \u26399 \u21270 \
    processor = SaunaDataProcessor()\
    \
    # \uc0\u12487 \u12540 \u12479 \u12398 \u35501 \u12415 \u36796 \u12415 \u12392 \u20998 \u26512 \u23455 \u34892 \
    with st.spinner('\uc0\u12487 \u12540 \u12479 \u20998 \u26512 \u12434 \u23455 \u34892 \u20013 ...'):\
        # \uc0\u20250 \u21729 \u12487 \u12540 \u12479 \
        if member_files:\
            member_path = file_paths[[f for f in member_files if 'delete' not in f][0]] if [f for f in member_files if 'delete' not in f] else None\
            member_delete_path = file_paths[[f for f in member_files if 'delete' in f][0]] if [f for f in member_files if 'delete' in f] else None\
            \
            if member_path:\
                processor.load_member_data(member_path, member_delete_path)\
                member_stats = processor.analyze_member_status()\
                \
                # \uc0\u20250 \u21729 \u12487 \u12540 \u12479 \u20998 \u26512 \u32080 \u26524 \u12398 \u34920 \u31034 \
                st.header('\uc0\u20250 \u21729 \u20998 \u26512 \u32080 \u26524 ')\
                col1, col2, col3 = st.columns(3)\
                col1.metric('\uc0\u20307 \u39443 \u20250 \u21729 \u25968 ', member_stats.get('trial_count', 0))\
                col2.metric('\uc0\u29694 \u20250 \u21729 \u25968 ', member_stats.get('current_members', 0))\
                col3.metric('\uc0\u36864 \u20250 \u20250 \u21729 \u25968 ', member_stats.get('former_members', 0))\
                \
                # \uc0\u24615 \u21029 \u20998 \u24067 \u12398 \u12464 \u12521 \u12501 \
                if 'gender_distribution' in member_stats and member_stats['gender_distribution']:\
                    st.subheader('\uc0\u24615 \u21029 \u20998 \u24067 ')\
                    fig, ax = plt.subplots()\
                    gender_data = member_stats['gender_distribution']\
                    ax.pie(gender_data.values(), labels=gender_data.keys(), autopct='%1.1f%%')\
                    st.pyplot(fig)\
                \
                # \uc0\u24180 \u40802 \u20998 \u24067 \
                if 'age_distribution' in member_stats:\
                    st.subheader('\uc0\u24180 \u40802 \u20998 \u24067 ')\
                    st.write(f"\uc0\u24179 \u22343 \u24180 \u40802 : \{member_stats['age_distribution'].get('mean', 'N/A'):.1f\}\u27507 ")\
        \
        # \uc0\u20104 \u32004 \u12487 \u12540 \u12479 \
        if reservation_files:\
            reservation_paths = [file_paths[f] for f in reservation_files]\
            processor.load_reservation_data(reservation_paths)\
            reservation_stats = processor.analyze_reservations()\
            \
            # \uc0\u20104 \u32004 \u12487 \u12540 \u12479 \u20998 \u26512 \u32080 \u26524 \u12398 \u34920 \u31034 \
            st.header('\uc0\u20104 \u32004 \u20998 \u26512 \u32080 \u26524 ')\
            if 'ticket_distribution' in reservation_stats:\
                st.subheader('\uc0\u12481 \u12465 \u12483 \u12488 \u31278 \u21029 \u20998 \u24067 ')\
                fig, ax = plt.subplots()\
                ticket_data = reservation_stats['ticket_distribution']\
                ax.bar(ticket_data.keys(), ticket_data.values())\
                plt.xticks(rotation=45)\
                st.pyplot(fig)\
            \
            # \uc0\u26376 \u21029 \u20104 \u32004 \u25968 \
            if 'monthly_stats' in reservation_stats:\
                st.subheader('\uc0\u26376 \u21029 \u20104 \u32004 \u25968 \u12398 \u25512 \u31227 ')\
                monthly_totals = \{\}\
                for ticket_type, monthly_data in reservation_stats['monthly_stats'].items():\
                    for month, count in monthly_data.items():\
                        month_str = str(month)\
                        if month_str in monthly_totals:\
                            monthly_totals[month_str] += count\
                        else:\
                            monthly_totals[month_str] = count\
                \
                fig, ax = plt.subplots(figsize=(10, 6))\
                months = sorted(monthly_totals.keys())\
                values = [monthly_totals[m] for m in months]\
                ax.plot(months, values, marker='o')\
                plt.xticks(rotation=45)\
                ax.set_xlabel('\uc0\u26376 ')\
                ax.set_ylabel('\uc0\u20104 \u32004 \u25968 ')\
                st.pyplot(fig)\
        \
        # \uc0\u31292 \u20685 \u29575 \u12487 \u12540 \u12479 \
        if frame_files:\
            frame_paths = [file_paths[f] for f in frame_files]\
            processor.load_frame_data(frame_paths)\
            occupancy_stats = processor.analyze_occupancy()\
            \
            # \uc0\u31292 \u20685 \u29575 \u20998 \u26512 \u32080 \u26524 \u12398 \u34920 \u31034 \
            st.header('\uc0\u31292 \u20685 \u29575 \u20998 \u26512 \u32080 \u26524 ')\
            for room, stats in occupancy_stats.items():\
                st.subheader(f'\{room\}\uc0\u12398 \u31292 \u20685 \u29575 ')\
                \
                # \uc0\u26376 \u21029 \u31292 \u20685 \u29575 \
                if 'monthly' in stats:\
                    st.write('\uc0\u26376 \u21029 \u24179 \u22343 \u31292 \u20685 \u29575 ')\
                    monthly = stats['monthly']\
                    if monthly:\
                        fig, ax = plt.subplots(figsize=(10, 6))\
                        months = sorted(monthly.keys())\
                        values = [monthly[m] * 100 for m in months]\
                        ax.plot(months, values, marker='o')\
                        plt.xticks(rotation=45)\
                        ax.set_xlabel('\uc0\u26376 ')\
                        ax.set_ylabel('\uc0\u31292 \u20685 \u29575  (%)')\
                        ax.set_ylim(0, 100)\
                        st.pyplot(fig)\
                \
                # \uc0\u26332 \u26085 \u21029 \u31292 \u20685 \u29575 \
                if 'weekday' in stats:\
                    st.write('\uc0\u26332 \u26085 \u21029 \u24179 \u22343 \u31292 \u20685 \u29575 ')\
                    weekday = stats['weekday']\
                    if weekday:\
                        weekday_jp = \{\
                            'Monday': '\uc0\u26376 \u26332 \u26085 ', 'Tuesday': '\u28779 \u26332 \u26085 ', 'Wednesday': '\u27700 \u26332 \u26085 ',\
                            'Thursday': '\uc0\u26408 \u26332 \u26085 ', 'Friday': '\u37329 \u26332 \u26085 ', 'Saturday': '\u22303 \u26332 \u26085 ', 'Sunday': '\u26085 \u26332 \u26085 '\
                        \}\
                        fig, ax = plt.subplots()\
                        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']\
                        days = [d for d in days if d in weekday]\
                        values = [weekday[d] * 100 for d in days]\
                        day_labels = [weekday_jp[d] for d in days]\
                        ax.bar(day_labels, values)\
                        ax.set_ylabel('\uc0\u31292 \u20685 \u29575  (%)')\
                        ax.set_ylim(0, 100)\
                        st.pyplot(fig)\
        \
        # \uc0\u22770 \u19978 \u12487 \u12540 \u12479 \
        if sales_files:\
            sales_paths = [file_paths[f] for f in sales_files]\
            processor.load_sales_data(sales_paths)\
            sales_stats = processor.analyze_sales()\
            \
            # \uc0\u22770 \u19978 \u20998 \u26512 \u32080 \u26524 \u12398 \u34920 \u31034 \
            st.header('\uc0\u22770 \u19978 \u20998 \u26512 \u32080 \u26524 ')\
            col1, col2 = st.columns(2)\
            col1.metric('\uc0\u32207 \u22770 \u19978 ', f'\{sales_stats.get("total_sales", 0):,\}\u20870 ')\
            col2.metric('\uc0\u24179 \u22343 \u21462 \u24341 \u38989 ', f'\{sales_stats.get("average_transaction", 0):,.0f\}\u20870 ')\
            \
            # \uc0\u26376 \u21029 \u22770 \u19978 \u25512 \u31227 \
            if 'monthly_sales' in sales_stats:\
                st.subheader('\uc0\u26376 \u21029 \u22770 \u19978 \u25512 \u31227 ')\
                monthly_sales = sales_stats['monthly_sales']\
                if monthly_sales:\
                    fig, ax = plt.subplots(figsize=(10, 6))\
                    months = sorted(monthly_sales.keys())\
                    values = [monthly_sales[m] for m in months]\
                    ax.plot(months, values, marker='o')\
                    plt.xticks(rotation=45)\
                    ax.set_xlabel('\uc0\u26376 ')\
                    ax.set_ylabel('\uc0\u22770 \u19978  (\u20870 )')\
                    st.pyplot(fig)\
                    \
                    # \uc0\u22770 \u19978 \u12488 \u12483 \u12503 5\u12398 \u26376 \
                    st.subheader('\uc0\u22770 \u19978 \u12488 \u12483 \u12503 5\u12398 \u26376 ')\
                    top_months = sorted(monthly_sales.items(), key=lambda x: x[1], reverse=True)[:5]\
                    top_data = \{str(month): sales for month, sales in top_months\}\
                    st.bar_chart(top_data)\
else:\
    st.info('\uc0\u12487 \u12540 \u12479 \u12501 \u12449 \u12452 \u12523 \u12434 \u12450 \u12483 \u12503 \u12525 \u12540 \u12489 \u12375 \u12390 \u12367 \u12384 \u12373 \u12356 ')}