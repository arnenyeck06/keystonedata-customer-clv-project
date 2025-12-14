"""
Data Upload Page for ChurnGuard Dashboard
Add this to your app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Import the data processor
from data_upload_processor import (
    DataUploadProcessor, 
    generate_predictions_for_upload,
    export_results_to_csv,
    export_results_to_excel
)


def show_data_upload_page():
    """
    Complete page for uploading customer data and getting predictions
    Add this function to your app.py and call it from the navigation
    """
    
    st.markdown('<div class="section-header">Upload Customer Data</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h3>Upload Your Customer Dataset</h3>
        <p style="color: #cbd5e0; margin-top: 0.5rem;">
            Upload a CSV or Excel file containing your customer data to get churn predictions for all customers at once.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize processor
    if 'upload_processor' not in st.session_state:
        st.session_state.upload_processor = DataUploadProcessor()
    
    processor = st.session_state.upload_processor
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📤 Upload Data", "📊 Results", "📋 Template"])
    
    # =============================
    # TAB 1: Upload Data
    # =============================
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Step 1: Upload Your File")
            
            uploaded_file = st.file_uploader(
                "Choose a CSV or Excel file",
                type=['csv', 'xlsx', 'xls'],
                help="Upload a file containing customer data with required columns: customer_id, tenure, monthly_charges"
            )
            
            if uploaded_file is not None:
                # Validate file
                is_valid, result = processor.validate_file(uploaded_file)
                
                if not is_valid:
                    st.error(result)
                else:
                    file_type = result
                    st.success(f"File validated: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
                    
                    # Load data
                    with st.spinner("Loading data..."):
                        success, message = processor.load_data(uploaded_file, file_type)
                        
                        if not success:
                            st.error(message)
                        else:
                            st.success(message)
                            
                            # Show data preview
                            st.markdown("### Step 2: Preview Your Data")
                            st.dataframe(processor.data.head(10), use_container_width=True, height=300)
                            
                            # Validate columns
                            st.markdown("### Step 3: Validate Columns")
                            processor.standardize_columns()
                            validation = processor.validate_columns()
                            
                            if validation['valid']:
                                st.success(validation['message'])
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("**✓ Required columns found:**")
                                    for col in processor.REQUIRED_COLUMNS:
                                        st.markdown(f"- {col}")
                                
                                with col_b:
                                    if validation.get('optional_present'):
                                        st.markdown("**+ Optional columns found:**")
                                        for col in validation['optional_present']:
                                            st.markdown(f"- {col}")
                                
                                # Clean data button
                                st.markdown("### Step 4: Process Data")
                                if st.button("🔄 Clean and Process Data", use_container_width=True):
                                    with st.spinner("Processing data..."):
                                        time.sleep(1)
                                        clean_results = processor.clean_data()
                                        
                                        if clean_results['success']:
                                            st.success("Data cleaned successfully!")
                                            
                                            # Show cleaning summary
                                            st.markdown("**Cleaning Summary:**")
                                            col1, col2, col3 = st.columns(3)
                                            
                                            with col1:
                                                st.metric("Original Rows", clean_results['original_rows'])
                                            with col2:
                                                st.metric("Duplicates Removed", clean_results['removed_duplicates'])
                                            with col3:
                                                st.metric("Final Rows", clean_results['final_rows'])
                                            
                                            # Get summary
                                            summary = processor.get_data_summary()
                                            
                                            st.markdown("**Data Summary:**")
                                            col1, col2, col3 = st.columns(3)
                                            
                                            with col1:
                                                st.metric("Total Customers", summary['total_customers'])
                                            with col2:
                                                st.metric("Avg Tenure", f"{summary['avg_tenure']:.1f} months")
                                            with col3:
                                                st.metric("Avg Monthly Charges", f"${summary['avg_monthly_charges']:.2f}")
                                            
                                            # Generate predictions button
                                            st.markdown("### Step 5: Generate Predictions")
                                            if st.button("🔮 Generate Churn Predictions", type="primary", use_container_width=True):
                                                with st.spinner("Generating predictions for all customers..."):
                                                    # Prepare data
                                                    prediction_data = processor.prepare_for_prediction()
                                                    
                                                    # Generate predictions
                                                    predictions_df = generate_predictions_for_upload(prediction_data)
                                                    
                                                    # Store in session state
                                                    st.session_state['upload_predictions'] = predictions_df
                                                    st.session_state['upload_timestamp'] = datetime.now()
                                                    
                                                    time.sleep(1)
                                                    st.success(f"✅ Generated predictions for {len(predictions_df)} customers!")
                                                    st.balloons()
                                                    st.info("📊 Go to the 'Results' tab to view and download your predictions")
                            else:
                                st.error(validation['message'])
                                st.markdown("**Columns in your file:**")
                                st.write(validation['present'])
                                st.markdown("**Required columns:**")
                                st.write(processor.REQUIRED_COLUMNS)
        
        with col2:
            st.markdown("### 📋 Requirements")
            
            st.markdown("""
            <div class="card">
                <h4 style="color: #4299e1; margin-bottom: 1rem;">Required Columns</h4>
                <ul style="color: #cbd5e0; line-height: 2;">
                    <li><code>customer_id</code></li>
                    <li><code>tenure</code></li>
                    <li><code>monthly_charges</code></li>
                </ul>
                
                <h4 style="color: #48bb78; margin: 1.5rem 0 1rem 0;">Optional Columns</h4>
                <ul style="color: #cbd5e0; line-height: 2; font-size: 0.9rem;">
                    <li><code>contract</code></li>
                    <li><code>payment_method</code></li>
                    <li><code>internet_service</code></li>
                    <li><code>total_charges</code></li>
                    <li>And more...</li>
                </ul>
                
                <h4 style="color: #ed8936; margin: 1.5rem 0 1rem 0;">File Requirements</h4>
                <ul style="color: #cbd5e0; line-height: 2;">
                    <li>Format: CSV or Excel</li>
                    <li>Max size: 50 MB</li>
                    <li>Max rows: Unlimited</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # =============================
    # TAB 2: Results
    # =============================
    with tab2:
        if 'upload_predictions' in st.session_state:
            predictions_df = st.session_state['upload_predictions']
            timestamp = st.session_state['upload_timestamp']
            
            st.markdown(f"### Prediction Results")
            st.markdown(f"<p style='color: #a0aec0;'>Generated on: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_customers = len(predictions_df)
            high_risk = len(predictions_df[predictions_df['risk_level'] == 'HIGH'])
            medium_risk = len(predictions_df[predictions_df['risk_level'] == 'MEDIUM'])
            low_risk = len(predictions_df[predictions_df['risk_level'] == 'LOW'])
            
            with col1:
                st.metric("Total Customers", total_customers)
            with col2:
                st.metric("High Risk", high_risk, delta=f"{high_risk/total_customers*100:.1f}%", delta_color="inverse")
            with col3:
                st.metric("Medium Risk", medium_risk, delta=f"{medium_risk/total_customers*100:.1f}%", delta_color="off")
            with col4:
                st.metric("Low Risk", low_risk, delta=f"{low_risk/total_customers*100:.1f}%", delta_color="normal")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Filter options
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_id = st.text_input("🔍 Search by Customer ID", placeholder="Enter customer ID")
            with col2:
                risk_filter = st.selectbox("Filter by Risk", ["All", "HIGH", "MEDIUM", "LOW"])
            with col3:
                sort_by = st.selectbox("Sort by", ["Probability (High to Low)", "Probability (Low to High)", "Customer ID"])
            
            # Apply filters
            filtered_df = predictions_df.copy()
            
            if search_id:
                filtered_df = filtered_df[filtered_df['customer_id'].str.contains(search_id, case=False)]
            
            if risk_filter != "All":
                filtered_df = filtered_df[filtered_df['risk_level'] == risk_filter]
            
            # Apply sorting
            if sort_by == "Probability (High to Low)":
                filtered_df = filtered_df.sort_values('churn_probability', ascending=False)
            elif sort_by == "Probability (Low to High)":
                filtered_df = filtered_df.sort_values('churn_probability', ascending=True)
            else:
                filtered_df = filtered_df.sort_values('customer_id')
            
            # Format for display
            display_df = filtered_df.copy()
            display_df['churn_probability'] = display_df['churn_probability'].apply(lambda x: f"{x*100:.1f}%")
            display_df['monthly_charges'] = display_df['monthly_charges'].apply(lambda x: f"${x:.2f}")
            
            # Rename columns for display
            display_df.columns = ['Customer ID', 'Churn Probability', 'Risk Level', 'Prediction', 'Tenure (months)', 'Monthly Charges']
            
            # Show results
            st.dataframe(
                display_df,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            st.markdown(f"<p style='color: #a0aec0;'>Showing {len(filtered_df)} of {total_customers} customers</p>", unsafe_allow_html=True)
            
            # Download options
            st.markdown("### 📥 Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv_data = export_results_to_csv(predictions_df)
                st.download_button(
                    label="📄 Download as CSV",
                    data=csv_data,
                    file_name=f"churn_predictions_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                excel_data = export_results_to_excel(predictions_df)
                st.download_button(
                    label="📊 Download as Excel",
                    data=excel_data,
                    file_name=f"churn_predictions_{timestamp.strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-text">No predictions yet</div>
                <p style="color: #718096; margin-top: 1rem;">Upload and process your data in the 'Upload Data' tab first</p>
            </div>
            """, unsafe_allow_html=True)
    
    # =============================
    # TAB 3: Template
    # =============================
    with tab3:
        st.markdown("### 📋 Download Sample Template")
        
        st.markdown("""
        <div class="card">
            <p style="color: #cbd5e0;">
                Not sure how to format your data? Download our sample template to see the required format.
                You can fill in your customer data and upload it back to get predictions.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate template
        template_df = processor.get_sample_template()
        
        st.markdown("### Template Preview")
        st.dataframe(template_df, use_container_width=True)
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            csv_template = export_results_to_csv(template_df)
            st.download_button(
                label="📄 Download Template (CSV)",
                data=csv_template,
                file_name="customer_data_template.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            excel_template = export_results_to_excel(template_df)
            st.download_button(
                label="📊 Download Template (Excel)",
                data=excel_template,
                file_name="customer_data_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        st.markdown("---")
        
        st.markdown("### 💡 Tips for Best Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="card">
                <h4 style="color: #4299e1;">Data Quality</h4>
                <ul style="color: #cbd5e0; line-height: 2;">
                    <li>Remove duplicate customer IDs</li>
                    <li>Ensure numeric fields are numbers</li>
                    <li>Fill in missing critical values</li>
                    <li>Use consistent formatting</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="card">
                <h4 style="color: #48bb78;">Column Names</h4>
                <ul style="color: #cbd5e0; line-height: 2;">
                    <li>Column names are case-insensitive</li>
                    <li>Spaces and underscores both work</li>
                    <li>Common variations are auto-detected</li>
                    <li>Extra columns are okay</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
