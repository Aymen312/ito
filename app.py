import streamlit as st
import pandas as pd
from io import BytesIO
import re
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Ayada TDR - Stock Manager", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════
# ENHANCED STYLING
# ═══════════════════════════════════════════════════════════════

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp { 
        background-color: #F8FAFC; 
    }
    
    /* Typography */
    h1 { 
        color: #0F172A; 
        font-weight: 700; 
        letter-spacing: -0.025em;
        font-size: 28px;
        margin-bottom: 1.5rem;
    }
    h2 { 
        color: #0F172A; 
        font-weight: 600; 
        font-size: 20px;
        margin-bottom: 1rem;
    }
    h3 { 
        color: #1E293B; 
        font-weight: 600; 
        font-size: 16px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF; 
        border-right: 1px solid #E2E8F0; 
        box-shadow: 2px 0 8px rgba(0,0,0,0.02); 
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #FFFFFF; 
        padding: 8px; 
        border-radius: 12px; 
        border: 1px solid #E2E8F0; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
        gap: 8px; 
    }
    .stTabs [data-baseweb="tab"] { 
        padding: 10px 18px; 
        border-radius: 8px !important; 
        border: none !important; 
        color: #64748B; 
        font-weight: 500; 
        background-color: transparent; 
        transition: all 0.2s ease-in-out; 
        font-size: 14px;
    }
    .stTabs [data-baseweb="tab"]:hover { 
        color: #0F172A; 
        background-color: #F1F5F9; 
    }
    .stTabs [aria-selected="true"] { 
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important; 
        color: #FFFFFF !important; 
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); 
    }
    
    /* Buttons */
    .stButton > button { 
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: #FFFFFF; 
        border: none; 
        border-radius: 8px; 
        padding: 10px 20px; 
        font-weight: 600; 
        transition: all 0.2s ease; 
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2); 
        width: 100%; 
    }
    .stButton > button:hover { 
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        box-shadow: 0 6px 12px -1px rgba(59, 130, 246, 0.3); 
    }
    
    /* Inputs */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div,
    .stSlider > div > div > div {
        border-radius: 8px; 
        border: 1.5px solid #CBD5E1; 
        padding: 10px 12px; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.02); 
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Expanders */
    [data-testid="stExpander"] { 
        background-color: #FFFFFF; 
        border-radius: 12px; 
        border: 1px solid #E2E8F0; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
    }
    
    /* File Upload */
    [data-testid="stFileUploadDropzone"] { 
        border: 2px dashed #CBD5E1; 
        border-radius: 12px; 
        background-color: #FFFFFF; 
    }
    [data-testid="stFileUploadDropzone"]:hover { 
        border-color: #3B82F6; 
        background-color: #EFF6FF; 
    }
    
    /* Tables */
    table { 
        border-collapse: collapse; 
        width: 100%; 
        background-color: white; 
        box-shadow: 0px 1px 3px rgba(0,0,0,0.08);
        border-radius: 8px; 
        overflow: hidden; 
    }
    th { 
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white; 
        font-weight: 600;
        font-size: 13px;
    }
    th, td { 
        padding: 14px 16px; 
        border-bottom: 1px solid #E2E8F0; 
        text-align: left;
    }
    tr:hover { 
        background-color: #F8FAFC; 
    }
    
    /* Metrics */
    .metric-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        text-align: center;
    }
    
    /* Alert Boxes */
    .alert-critical {
        background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
        border-left: 4px solid #DC2626;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    .alert-warning {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    .alert-success {
        background: linear-gradient(135deg, #DCFCE7 0%, #BBFBEE 100%);
        border-left: 4px solid #10B981;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    
    /* Badge */
    .badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .badge-critical { background: #FEE2E2; color: #991B1B; }
    .badge-warning { background: #FEF3C7; color: #92400E; }
    .badge-success { background: #DCFCE7; color: #065F46; }
    .badge-info { background: #DBEAFE; color: #0C4A6E; }
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def clean_numeric_columns(df):
    for col in ['Prix Achat', 'Qté stock dispo', 'Valeur Stock']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    return df

def clean_size_column(df):
    if 'taille' in df.columns:
        df['taille'] = df['taille'].astype(str).str.strip()
    return df

def highlight_critical_qty(val):
    """Red for qty=1, amber for qty<5"""
    if val == 1:
        return 'background-color: #FEE2E2; color: #991B1B; font-weight: 600;'
    elif 1 < val < 5:
        return 'background-color: #FEF3C7; color: #92400E;'
    return ''

def highlight_negative(val):
    """Red for negative stock"""
    if val < 0:
        return 'background-color: #FEE2E2; color: #991B1B; font-weight: 600;'
    return ''

def get_stock_health(df):
    """Calculate stock health metrics"""
    total_skus = len(df)
    total_qty = df['Qté stock dispo'].sum()
    total_value = df['Valeur Stock'].sum() if 'Valeur Stock' in df.columns else 0
    critical_items = len(df[df['Qté stock dispo'] == 1])
    low_stock = len(df[(df['Qté stock dispo'] > 1) & (df['Qté stock dispo'] < 5)])
    negative_items = len(df[df['Qté stock dispo'] < 0])
    
    return {
        'total_skus': total_skus,
        'total_qty': total_qty,
        'total_value': total_value,
        'critical_items': critical_items,
        'low_stock': low_stock,
        'negative_items': negative_items
    }

def display_kpi_dashboard(health):
    """Display KPI metrics at top"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total SKUs",
            value=f"{health['total_skus']:,}",
            delta=None,
            help="Total number of unique products"
        )
    
    with col2:
        st.metric(
            label="📊 Total Qty",
            value=f"{health['total_qty']:,.0f}",
            help="Total units in stock across all products"
        )
    
    with col3:
        st.metric(
            label="💰 Stock Value",
            value=f"€{health['total_value']:,.0f}",
            help="Total stock value at cost (HT)"
        )
    
    with col4:
        pct_critical = (health['critical_items'] / health['total_skus'] * 100) if health['total_skus'] > 0 else 0
        color = "🔴" if pct_critical > 10 else "🟡" if pct_critical > 5 else "🟢"
        st.metric(
            label=f"{color} Critical Items",
            value=f"{health['critical_items']}",
            delta=f"{pct_critical:.1f}% of stock",
            help="Items with Qty = 1"
        )

def display_alerts(health):
    """Display alert boxes for critical issues"""
    alerts = []
    
    if health['negative_items'] > 0:
        alerts.append({
            'type': 'critical',
            'title': f"⚠️ {health['negative_items']} Items with Negative Stock",
            'message': 'Immediately review items with negative quantities',
            'action': 'negative'
        })
    
    if health['critical_items'] > health['total_skus'] * 0.15:
        alerts.append({
            'type': 'warning',
            'title': f"⚠️ {health['critical_items']} Critical Items (Qty = 1)",
            'message': 'Many items are running on single unit reserves',
            'action': 'critical'
        })
    
    if health['low_stock'] > health['total_skus'] * 0.20:
        alerts.append({
            'type': 'warning',
            'title': f"📌 {health['low_stock']} Items Low Stock (Qty < 5)",
            'message': 'Consider reordering items below 5 units',
            'action': 'low'
        })
    
    for alert in alerts:
        if alert['type'] == 'critical':
            st.markdown(f'<div class="alert-critical"><strong>{alert["title"]}</strong><br/>{alert["message"]}</div>', unsafe_allow_html=True)
        elif alert['type'] == 'warning':
            st.markdown(f'<div class="alert-warning"><strong>{alert["title"]}</strong><br/>{alert["message"]}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# VISUALIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def create_supplier_value_donut(df):
    """Create interactive donut chart of supplier values"""
    supplier_value = df.groupby('fournisseur')['Valeur Stock'].sum().sort_values(ascending=False).head(10)
    
    fig = go.Figure(data=[go.Pie(
        labels=supplier_value.index,
        values=supplier_value.values,
        hole=0.4,
        marker=dict(
            colors=['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', 
                   '#06B6D4', '#EC4899', '#14B8A6', '#F97316', '#6366F1']
        ),
        hovertemplate='<b>%{label}</b><br>€%{value:,.2f}<br>%{percent}<extra></extra>',
        textposition='inside',
        textinfo='label+percent'
    )])
    
    fig.update_layout(
        title='Top 10 Suppliers by Stock Value',
        height=400,
        showlegend=True,
        template='plotly_white',
        font=dict(family='Inter, sans-serif', size=12, color='#0F172A'),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_category_distribution(df):
    """Create bar chart of stock by category"""
    if 'famille' not in df.columns:
        return None
    
    category_qty = df.groupby('famille')['Qté stock dispo'].sum().sort_values(ascending=True)
    
    fig = go.Figure(data=[go.Bar(
        y=category_qty.index,
        x=category_qty.values,
        orientation='h',
        marker=dict(color='#3B82F6'),
        hovertemplate='<b>%{y}</b><br>%{x:,.0f} units<extra></extra>'
    )])
    
    fig.update_layout(
        title='Stock Quantity by Category',
        height=300,
        showlegend=False,
        template='plotly_white',
        font=dict(family='Inter, sans-serif', size=12, color='#0F172A'),
        xaxis_title='Quantity',
        yaxis_title='',
        margin=dict(l=150, r=20, t=40, b=20)
    )
    
    return fig

def create_size_heatmap(df, designation):
    """Create heatmap of sizes by supplier for a designation"""
    if 'taille' not in df.columns or 'fournisseur' not in df.columns:
        return None
    
    df_design = df[df['designation'].str.upper() == designation.upper()] if designation else df
    
    if df_design.empty:
        return None
    
    pivot_data = pd.crosstab(
        df_design['taille'],
        df_design['fournisseur'],
        values=df_design['Qté stock dispo'],
        aggfunc='sum',
        fill_value=0
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlGn',
        hovertemplate='Size: %{y}<br>Supplier: %{x}<br>Qty: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Size Distribution - {designation}',
        height=400,
        template='plotly_white',
        font=dict(family='Inter, sans-serif', size=12),
        margin=dict(l=80, r=20, t=40, b=80)
    )
    
    return fig

# ═══════════════════════════════════════════════════════════════
# STOCK ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def filter_negative_stock(df):
    df['Qté stock dispo'] = df['Qté stock dispo'].fillna(0)
    df_neg = df[df['Qté stock dispo'] < 0].copy()
    return df_neg[['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'Qté stock dispo', 'Valeur Stock']]

def display_supplier_info(df, fournisseur):
    colonnes_afficher = ['fournisseur', 'barcode', 'couleur', 'taille', 'designation', 'rayon', 'marque', 'famille', 'Qté stock dispo', 'Valeur Stock']
    fournisseur = fournisseur.strip().upper()
    df['fournisseur'] = df['fournisseur'].fillna('')
    df_filtered = df[df['fournisseur'].str.upper() == fournisseur] if fournisseur else pd.DataFrame(columns=colonnes_afficher)
    
    if not df_filtered.empty:
        designations_rayons = df_filtered.groupby(['designation', 'rayon']).size().reset_index(name='Nombre de références')
        designations_rayons = designations_rayons.sort_values(['designation', 'rayon'])
        
        with st.expander(f"📋 Désignations pour {fournisseur}", expanded=True):
            designations_rayons['selection'] = designations_rayons.apply(lambda x: f"{x['designation']} ({x['rayon']})", axis=1)
            selected = st.selectbox("Sélectionnez une désignation", designations_rayons['selection'], key=f"sup_{fournisseur}")
            selected_design, selected_rayon = selected.split(" (")
            selected_rayon = selected_rayon[:-1]
            
            filtered = df_filtered[(df_filtered['designation'] == selected_design) & (df_filtered['rayon'] == selected_rayon)]
            
            if not filtered.empty:
                st.subheader(f"{selected_design} - {selected_rayon}")
                styled_df = filtered[colonnes_afficher].style.applymap(
                    lambda x: highlight_critical_qty(x) if isinstance(x, (int, float)) and x == int(x) else '',
                    subset=['Qté stock dispo']
                )
                st.dataframe(styled_df, use_container_width=True, height=400)
    
    return df_filtered[colonnes_afficher] if not df_filtered.empty else pd.DataFrame(columns=colonnes_afficher)

def display_designation_info(df, designation):
    colonnes_a_afficher = ['barcode', 'taille', 'rayon', 'couleur', 'designation', 'Qté stock dispo']
    designation = designation.strip().upper()
    df['designation'] = df['designation'].fillna('')
    df_filtered = df[df['designation'].str.upper() == designation] if designation else pd.DataFrame(columns=colonnes_a_afficher)
    
    if not df_filtered.empty:
        df_display = df_filtered[colonnes_a_afficher].copy()
        styled_df = df_display.style.applymap(
            lambda x: highlight_critical_qty(x) if isinstance(x, (int, float)) and x == int(x) else '',
            subset=['Qté stock dispo']
        )
        st.dataframe(styled_df, use_container_width=True)
        
        # Show heatmap
        fig = create_size_heatmap(df, designation)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

def total_stock_value_by_supplier(df):
    df['Qté stock dispo'] = pd.to_numeric(df['Qté stock dispo'], errors='coerce').fillna(0)
    df['Prix Achat'] = pd.to_numeric(df['Prix Achat'], errors='coerce').fillna(0)
    df['Valeur Totale HT'] = df['Qté stock dispo'] * df['Prix Achat']
    total_value_by_supplier = df.groupby('fournisseur')['Valeur Totale HT'].sum().reset_index()
    return total_value_by_supplier.sort_values(by='Valeur Totale HT', ascending=False)

def display_stock_by_family(df):
    familles = ["CHAUSSURES RANDO", "CHAUSSURES RUNN", "CHAUSSURE TRAIL"]
    for famille in familles:
        st.subheader(f"👟 {famille}")
        df['famille'] = df['famille'].fillna('')
        df_family = df[df['famille'].str.upper() == famille]
        
        if not df_family.empty:
            total_stock = df_family['Qté stock dispo'].sum()
            total_value = df_family['Valeur Stock'].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("📦 Quantity", f"{int(total_stock):,} units", help="Total units in this category")
            col2.metric("💰 Value", f"€{total_value:,.0f}", help="Total value at cost")
            
            rayon_filter = st.selectbox(f"Filter by gender:", ['All', 'Homme', 'Femme', 'Other'], key=f"rayon_{famille}")
            if rayon_filter != 'All':
                df_family['rayon'] = df_family['rayon'].fillna('')
                if rayon_filter in ['Homme', 'Femme']:
                    df_family = df_family[df_family['rayon'].str.upper() == rayon_filter.upper()]
            
            if not df_family.empty:
                styled_df = df_family[['rayon', 'fournisseur', 'couleur', 'taille', 'designation', 'marque', 'Qté stock dispo', 'Valeur Stock']].style.applymap(
                    lambda x: highlight_critical_qty(x) if isinstance(x, (int, float)) and x == int(x) else '',
                    subset=['Qté stock dispo']
                )
                st.dataframe(styled_df, use_container_width=True)
        
        st.divider()

# ═══════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════

st.title("🎯 Ayada TDR - Advanced Stock Manager")

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3081/3081840.png", width=50)
st.sidebar.markdown("### 📂 Data Import")
st.sidebar.info("Upload your stock file to begin analysis")
fichier_telecharge = st.sidebar.file_uploader("Stock file (CSV/XLSX)", type=['csv', 'xlsx'])

if fichier_telecharge is not None:
    extension_fichier = fichier_telecharge.name.split('.')[-1]
    
    try:
        with st.spinner("⏳ Loading and processing data..."):
            if extension_fichier == 'csv':
                df = pd.read_csv(fichier_telecharge, encoding='ISO-8859-1', sep=';')
            elif extension_fichier == 'xlsx':
                df = pd.read_excel(fichier_telecharge)
            else:
                st.error("❌ Unsupported file format")
                df = None
            
            if df is not None:
                df = clean_numeric_columns(df)
                df = clean_size_column(df)
                st.success("✅ Data loaded successfully!")
                
                # Calculate health metrics
                health = get_stock_health(df)
                
                # Display KPI Dashboard
                st.markdown("## 📊 Stock Health Dashboard")
                display_kpi_dashboard(health)
                
                st.divider()
                
                # Display Alerts
                display_alerts(health)
                
                st.divider()
                
                # Create tabs
                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                    "💰 Supplier Values",
                    "🏢 Supplier Details",
                    "🔍 Model Search",
                    "⚠️ Negative Stock",
                    "📦 Categories",
                    "👟 Size Analysis",
                    "📈 Analytics",
                    "⚙️ Export"
                ])
                
                # TAB 1: Supplier Values
                with tab1:
                    st.markdown("### Top Suppliers by Stock Value")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        fig_donut = create_supplier_value_donut(df)
                        st.plotly_chart(fig_donut, use_container_width=True)
                    
                    with col2:
                        st.markdown("**Top 10 Suppliers**")
                        df_tv = total_stock_value_by_supplier(df)
                        for idx, row in df_tv.head(10).iterrows():
                            st.metric(
                                row['fournisseur'].upper(),
                                f"€{row['Valeur Totale HT']:,.0f}"
                            )
                
                # TAB 2: Supplier Details
                with tab2:
                    st.markdown("### Search by Supplier")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        fournisseur = st.text_input("📍 Supplier name:", placeholder="e.g., New Balance, Salomon...")
                    with col2:
                        st.write("")
                        if st.button("🔍 Search", use_container_width=True):
                            st.session_state.search_supplier = fournisseur
                    
                    if fournisseur:
                        df_filtered = display_supplier_info(df.copy(), fournisseur)
                        if df_filtered.empty:
                            st.warning(f"❌ No supplier found matching '{fournisseur}'")
                
                # TAB 3: Model Search
                with tab3:
                    st.markdown("### Search by Product Model")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        designation = st.text_input("🏷️ Model name:", placeholder="e.g., Clifton, Brooks Ghost...")
                    with col2:
                        st.write("")
                        if st.button("🔍 Find", use_container_width=True):
                            st.session_state.search_model = designation
                    
                    if designation:
                        display_designation_info(df.copy(), designation)
                
                # TAB 4: Negative Stock
                with tab4:
                    st.markdown("### 🚨 Items with Negative Stock")
                    
                    df_neg = filter_negative_stock(df.copy())
                    
                    if df_neg.empty:
                        st.success("✅ No negative stock items!")
                    else:
                        st.error(f"⚠️ {len(df_neg)} items with negative quantity")
                        
                        styled_df = df_neg.style.applymap(
                            lambda x: 'background-color: #FEE2E2; color: #991B1B; font-weight: 600;' if x < 0 else '',
                            subset=['Qté stock dispo']
                        )
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # Export negative items
                        csv = df_neg.to_csv(index=False, sep=';')
                        st.download_button(
                            "⬇️ Export Negative Items (CSV)",
                            csv,
                            "negative_items.csv",
                            "text/csv",
                            use_container_width=True
                        )
                
                # TAB 5: Categories
                with tab5:
                    st.markdown("### Stock by Category")
                    display_stock_by_family(df.copy())
                
                # TAB 6: Size Analysis
                with tab6:
                    st.markdown("### Size Distribution Analysis")
                    
                    if 'designation' in df.columns:
                        designations = sorted([d for d in df['designation'].unique() if pd.notna(d)])
                        selected_design = st.selectbox("Select product:", designations)
                        
                        if selected_design:
                            fig = create_size_heatmap(df, selected_design)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                
                # TAB 7: Analytics
                with tab7:
                    st.markdown("### 📈 Stock Analytics")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_cat = create_category_distribution(df)
                        if fig_cat:
                            st.plotly_chart(fig_cat, use_container_width=True)
                    
                    with col2:
                        st.markdown("### Quantity Distribution")
                        qty_stats = {
                            'Critical (=1)': len(df[df['Qté stock dispo'] == 1]),
                            'Low (2-4)': len(df[(df['Qté stock dispo'] >= 2) & (df['Qté stock dispo'] <= 4)]),
                            'Medium (5-10)': len(df[(df['Qté stock dispo'] >= 5) & (df['Qté stock dispo'] <= 10)]),
                            'Good (11-20)': len(df[(df['Qté stock dispo'] >= 11) & (df['Qté stock dispo'] <= 20)]),
                            'Excellent (>20)': len(df[df['Qté stock dispo'] > 20]),
                            'Negative': len(df[df['Qté stock dispo'] < 0])
                        }
                        
                        for label, count in qty_stats.items():
                            if label == 'Critical (=1)':
                                st.metric(f"🔴 {label}", count)
                            elif label == 'Low (2-4)':
                                st.metric(f"🟠 {label}", count)
                            elif label == 'Negative':
                                st.metric(f"⚫ {label}", count)
                            else:
                                st.metric(f"🟢 {label}", count)
                
                # TAB 8: Export
                with tab8:
                    st.markdown("### 📥 Export Data")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Current View")
                        csv = df.to_csv(index=False, sep=';')
                        st.download_button(
                            "⬇️ CSV Export",
                            csv,
                            "stock_export.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        st.subheader("Excel with Formatting")
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df.to_excel(writer, sheet_name='Stock', index=False)
                        st.download_button(
                            "⬇️ Excel Export",
                            buffer.getvalue(),
                            "stock_export.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    st.divider()
                    st.markdown("### Filter & Export")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        show_critical = st.checkbox("Only Critical Items (Qty=1)", value=False)
                        show_negative = st.checkbox("Only Negative Stock", value=False)
                    
                    with col2:
                        show_low = st.checkbox("Only Low Stock (<5)", value=False)
                    
                    export_df = df.copy()
                    if show_critical:
                        export_df = export_df[export_df['Qté stock dispo'] == 1]
                    if show_negative:
                        export_df = export_df[export_df['Qté stock dispo'] < 0]
                    if show_low:
                        export_df = export_df[export_df['Qté stock dispo'] < 5]
                    
                    if not export_df.empty:
                        csv_filtered = export_df.to_csv(index=False, sep=';')
                        st.download_button(
                            f"⬇️ Export Filtered ({len(export_df)} items)",
                            csv_filtered,
                            "stock_filtered.csv",
                            "text/csv",
                            use_container_width=True
                        )
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.info("Please check your file format and try again.")

else:
    st.info("👈 Use the sidebar to upload your stock file (CSV or XLSX)")
