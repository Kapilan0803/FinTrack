// Enhanced Vasool Drive App
class VasoolDriveApp {
    constructor() {
        this.borrowers = [];
        this.payments = [];
        this.investments = [];
        this.nextId = 1;
        this.nextPaymentId = 1;
        this.currentSection = 'dashboard';
        this.currentCustomerId = null;
        this.branches = {
            main: 'Main Branch',
            branch2: 'Branch 2',
            branch3: 'Branch 3'
        };
        this.currentBranch = 'main';
        this.init();
    }

    init() {
        this.loadSampleData();
        this.updateDate();
        this.bindEvents();
        this.loadSectionContent('dashboard');
        setInterval(() => this.updateDate(), 1000);
    }

    loadSampleData() {
        // Add some sample borrowers for demonstration
        const sampleBorrowers = [
            {
                id: this.nextId++,
                name: 'Ravi Kumar',
                phone: '9876543210',
                address: 'Salem, TN',
                loanAmount: 50000,
                interestRate: 2,
                interestType: 'monthly',
                loanType: 'monthly',
                date: '2024-01-15',
                totalAmount: 60000,
                paidAmount: 15000,
                payableAmount: 45000,
                status: 'active',
                dueDate: '2024-08-15'
            },
            {
                id: this.nextId++,
                name: 'Priya Devi',
                phone: '9123456789',
                address: 'Coimbatore, TN',
                loanAmount: 25000,
                interestRate: 1.5,
                interestType: 'monthly',
                loanType: 'daily',
                date: '2024-02-01',
                totalAmount: 27500,
                paidAmount: 27500,
                payableAmount: 0,
                status: 'completed',
                dueDate: '2024-07-01'
            }
        ];
        this.borrowers = sampleBorrowers;
        this.nextId = 3;
    }

    updateDate() {
        const now = new Date();
        
        // Format date
        const dateStr = now.toLocaleDateString('en-IN', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        
        // Format time with seconds
        const timeStr = now.toLocaleTimeString('en-IN', {
            hour12: true,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // Update displays
        document.getElementById('currentDate').textContent = dateStr;
        const timeDisplay = document.getElementById('currentTime');
        if (timeDisplay) {
            timeDisplay.textContent = timeStr;
        }
    }

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.closest('[data-section]').dataset.section;
                this.switchSection(section);
            });
        });

        // Branch selector
        const branchSelector = document.getElementById('branchSelector');
        if (branchSelector) {
            branchSelector.addEventListener('change', (e) => {
                this.currentBranch = e.target.value;
                this.showSuccessMessage(`Switched to ${this.branches[this.currentBranch]}`);
            });
        }
    }

    switchSection(section) {
        // Update active nav
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');

        this.currentSection = section;
        this.loadSectionContent(section);
    }

    loadSectionContent(section) {
        const contentArea = document.getElementById('content-area');
        
        switch(section) {
            case 'dashboard':
                this.loadDashboard(contentArea);
                break;
            case 'customer':
                this.loadCustomerSection(contentArea);
                break;
            case 'collection':
                this.loadCollectionSection(contentArea);
                break;
            case 'daily':
                this.loadLoanTypeSection(contentArea, 'Daily Loans', 'daily');
                break;
            case 'monthly':
                this.loadLoanTypeSection(contentArea, 'Monthly Loans', 'monthly');
                break;
            case 'investment':
                this.loadInvestmentSection(contentArea);
                break;
            case 'reports':
                this.loadReportsSection(contentArea);
                break;
            case 'cashout':
                this.loadCashoutSection(contentArea);
                break;
            default:
                this.loadComingSoon(contentArea, section);
        }
    }

    loadDashboard(contentArea) {
        const totalLoanAmount = this.borrowers.reduce((sum, b) => sum + b.loanAmount, 0);
        const totalPaidAmount = this.borrowers.reduce((sum, b) => sum + b.paidAmount, 0);
        const totalOutstanding = this.borrowers.reduce((sum, b) => sum + b.payableAmount, 0);
        const activeBorrowers = this.borrowers.filter(b => b.status === 'active').length;
        const completedLoans = this.borrowers.filter(b => b.status === 'completed').length;
        const overdueLoans = this.borrowers.filter(b => this.isOverdue(b)).length;

        contentArea.innerHTML = `
            <div class="content-header">
                <h2 class="content-title">Dashboard</h2>
                <p class="content-subtitle">Overview of your loan management system</p>
            </div>

            <div class="quick-actions">
                <button class="quick-action-btn btn-primary" onclick="app.switchSection('customer')">
                    <span>👥</span> Add Customer
                </button>
                <button class="quick-action-btn btn-success" onclick="app.switchSection('collection')">
                    <span>💸</span> Record Payment
                </button>
                <button class="quick-action-btn btn-warning" onclick="app.switchSection('reports')">
                    <span>📋</span> View Reports
                </button>
                <button class="quick-action-btn btn-secondary" onclick="app.switchSection('investment')">
                    <span>📈</span> Investment
                </button>
            </div>

            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-icon">👥</div>
                    <div class="stat-value">${this.borrowers.length}</div>
                    <div class="stat-label">Total Customers</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-icon">💰</div>
                    <div class="stat-value">₹${totalLoanAmount.toLocaleString('en-IN')}</div>
                    <div class="stat-label">Total Loans</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-icon">💸</div>
                    <div class="stat-value">₹${totalPaidAmount.toLocaleString('en-IN')}</div>
                    <div class="stat-label">Collected Amount</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-icon">⏰</div>
                    <div class="stat-value">₹${totalOutstanding.toLocaleString('en-IN')}</div>
                    <div class="stat-label">Outstanding</div>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-icon">🔄</div>
                    <div class="stat-value">${activeBorrowers}</div>
                    <div class="stat-label">Active Loans</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-icon">✅</div>
                    <div class="stat-value">${completedLoans}</div>
                    <div class="stat-label">Completed Loans</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-icon">⚠️</div>
                    <div class="stat-value">${overdueLoans}</div>
                    <div class="stat-label">Overdue Loans</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-icon">📊</div>
                    <div class="stat-value">${((totalPaidAmount / totalLoanAmount) * 100 || 0).toFixed(1)}%</div>
                    <div class="stat-label">Collection Rate</div>
                </div>
            </div>

            <div class="table-container">
                <div class="table-header">📈 Recent Activities</div>
                <div class="table">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Customer</th>
                                <th>Loan Amount</th>
                                <th>Outstanding</th>
                                <th>Status</th>
                                <th>Due Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.borrowers.slice(0, 5).map(borrower => `
                                <tr>
                                    <td><strong>${borrower.name}</strong><br><small>${borrower.phone}</small></td>
                                    <td class="amount">₹${borrower.loanAmount.toLocaleString('en-IN')}</td>
                                    <td class="amount ${borrower.payableAmount > 0 ? 'negative' : ''}">₹${borrower.payableAmount.toLocaleString('en-IN')}</td>
                                    <td><span class="status-badge status-${borrower.status}">${borrower.status}</span></td>
                                    <td>${borrower.dueDate || '-'}</td>
                                    <td>
                                        <button class="action-btn btn-pay" onclick="app.quickPayment(${borrower.id})">💸</button>
                                        <button class="action-btn btn-view" onclick="app.viewBorrower(${borrower.id})">👁️</button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    loadCustomerSection(contentArea) {
        contentArea.innerHTML = `
            <div class="content-header">
                <h2 class="content-title">Customer Management</h2>
                <p class="content-subtitle">Add and manage your borrowers</p>
            </div>

            <div class="form-container">
                <h3 style="margin-bottom: 1.5rem; color: #2c3e50;">Add New Borrower</h3>
                <form id="borrowerForm">
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label" for="name">Customer Name *</label>
                            <input type="text" id="name" name="name" class="form-input required" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="phone">Phone Number</label>
                            <input type="tel" id="phone" name="phone" class="form-input" pattern="[0-9]{10}">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="address">Address</label>
                            <input type="text" id="address" name="address" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="loanType">Loan Type *</label>
                            <select id="loanType" name="loanType" class="form-input required" required>
                                <option value="">Select loan type...</option>
                                <option value="daily">Daily Collection</option>
                                <option value="weekly">Weekly Collection</option>
                                <option value="monthly">Monthly Collection</option>
                                <option value="enterprise">Enterprise Loan</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="loanAmount">Loan Amount *</label>
                            <input type="number" id="loanAmount" name="loanAmount" class="form-input required" min="1000" step="500" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="interestRate">Interest Rate (%) *</label>
                            <input type="number" id="interestRate" name="interestRate" class="form-input required" min="0.5" max="10" step="0.1" value="2" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="interestType">Interest Type *</label>
                            <select id="interestType" name="interestType" class="form-input required" required>
                                <option value="monthly">Monthly</option>
                                <option value="daily">Daily</option>
                                <option value="simple">Simple Interest</option>
                                <option value="compound">Compound Interest</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="duration">Duration (Months)</label>
                            <input type="number" id="duration" name="duration" class="form-input" min="1" max="60" value="6">
                        </div>
                    </div>
                    <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                        <button type="submit" class="btn btn-primary">
                            <span class="btn-text">Add Customer</span>
                            <span class="loading" style="display: none;"></span>
                        </button>
                        <button type="reset" class="btn btn-secondary">Clear Form</button>
                    </div>
                </form>
            </div>

            <div class="table-container">
                <div class="table-header">👥 Customer List</div>
                <div id="customersTableContainer">
                    ${this.generateCustomersTable()}
                </div>
            </div>
        `;
        this.bindCustomerForm();
    }

    loadCollectionSection(contentArea) {
        contentArea.innerHTML = `
            <div class="content-header">
                <h2 class="content-title">Collection Management</h2>
                <p class="content-subtitle">Record payments and manage collections</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card success">
                    <div class="stat-icon">💰</div>
                    <div class="stat-value">₹${this.getTodayCollection().toLocaleString('en-IN')}</div>
                    <div class="stat-label">Today's Collection</div>
                </div>
                <div class="stat-card primary">
                    <div class="stat-icon">📅</div>
                    <div class="stat-value">₹${this.getMonthlyCollection().toLocaleString('en-IN')}</div>
                    <div class="stat-label">This Month</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-icon">⏰</div>
                    <div class="stat-value">${this.getDueTodayCount()}</div>
                    <div class="stat-label">Due Today</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-icon">⚠️</div>
                    <div class="stat-value">${this.getOverdueCount()}</div>
                    <div class="stat-label">Overdue</div>
                </div>
            </div>

            <div class="form-container">
                <h3 style="margin-bottom: 1.5rem; color: #2c3e50;">Record Payment</h3>
                <form id="paymentForm">
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Select Customer *</label>
                            <select class="form-input required" id="paymentCustomer" required>
                                <option value="">Choose customer...</option>
                                ${this.borrowers.filter(b => b.payableAmount > 0).map(b => 
                                    `<option value="${b.id}">${b.name} (#${String(b.id).padStart(4, '0')}) - Outstanding: ₹${b.payableAmount.toLocaleString('en-IN')}</option>`
                                ).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Payment Amount *</label>
                            <input type="number" class="form-input required" id="paymentAmount" min="1" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Payment Date *</label>
                            <input type="date" class="form-input required" id="paymentDate" value="${new Date().toISOString().split('T')[0]}" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Payment Method</label>
                            <select class="form-input" id="paymentMethod">
                                <option value="cash">Cash</option>
                                <option value="bank">Bank Transfer</option>
                                <option value="upi">UPI</option>
                                <option value="cheque">Cheque</option>
                                <option value="card">Card</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Reference Number</label>
                            <input type="text" class="form-input" id="paymentReference" placeholder="Transaction ID, Cheque No., etc.">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes</label>
                            <input type="text" class="form-input" id="paymentNotes" placeholder="Additional notes...">
                        </div>
                    </div>
                    <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                        <button type="submit" class="btn btn-primary">
                            <span class="btn-text">Record Payment</span>
                            <span class="loading" style="display: none;"></span>
                        </button>
                        <button type="reset" class="btn btn-secondary">Clear Form</button>
                    </div>
                </form>
            </div>

            <div class="table-container">
                <div class="table-header">💸 Recent Collections</div>
                <div>
                    ${this.generatePaymentsTable()}
                </div>
            </div>
        `;
        this.bindPaymentForm();
    }

    loadReportsSection(contentArea) {
        const totalLoanAmount = this.borrowers.reduce((sum, b) => sum + b.loanAmount, 0);
        const totalCollected = this.borrowers.reduce((sum, b) => sum + b.paidAmount, 0);
        const totalOutstanding = this.borrowers.reduce((sum, b) => sum + b.payableAmount, 0);

        contentArea.innerHTML = `
            <div class="content-header">
                <h2 class="content-title">Reports & Analytics</h2>
                <p class="content-subtitle">Comprehensive business insights</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-icon">📊</div>
                    <div class="stat-value">₹${totalLoanAmount.toLocaleString('en-IN')}</div>
                    <div class="stat-label">Total Loans Disbursed</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-icon">💰</div>
                    <div class="stat-value">₹${totalCollected.toLocaleString('en-IN')}</div>
                    <div class="stat-label">Total Collections</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-icon">⏳</div>
                    <div class="stat-value">₹${totalOutstanding.toLocaleString('en-IN')}</div>
                    <div class="stat-label">Outstanding Amount</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-icon">📈</div>
                    <div class="stat-value">${((totalCollected / totalLoanAmount) * 100 || 0).toFixed(1)}%</div>
                    <div class="stat-label">Recovery Rate</div>
                </div>
            </div>

            <div class="form-container">
                <h3 style="margin-bottom: 1.5rem;">Generate Reports</h3>
                <div class="quick-actions">
                    <button class="quick-action-btn btn-primary" onclick="app.generateReport('daily')">
                        <span>📅</span> Daily Report
                    </button>
                    <button class="quick-action-btn btn-success" onclick="app.generateReport('monthly')">
                        <span>📆</span> Monthly Report
                    </button>
                    <button class="quick-action-btn btn-warning" onclick="app.generateReport('customer')">
                        <span>👥</span> Customer Report
                    </button>
                    <button class="quick-action-btn btn-secondary" onclick="app.generateReport('collection')">
                        <span>💸</span> Collection Report
                    </button>
                </div>
            </div>

            <div class="table-container">
                <div class="table-header">📋 Loan Performance Summary</div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Loan Type</th>
                            <th>Total Loans</th>
                            <th>Amount Disbursed</th>
                            <th>Amount Collected</th>
                            <th>Outstanding</th>
                            <th>Recovery %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.generateLoanSummary()}
                    </tbody>
                </table>
            </div>
        `;
    }

    // Utility Functions
    isOverdue(borrower) {
        if (!borrower.dueDate) return false;
        const dueDate = new Date(borrower.dueDate);
        const today = new Date();
        return dueDate < today && borrower.payableAmount > 0;
    }

    getTodayCollection() {
        const today = new Date().toISOString().split('T')[0];
        return this.payments
            .filter(p => p.date === today)
            .reduce((sum, p) => sum + p.amount, 0);
    }

    getMonthlyCollection() {
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        return this.payments
            .filter(p => {
                const paymentDate = new Date(p.date);
                return paymentDate.getMonth() === currentMonth && paymentDate.getFullYear() === currentYear;
            })
            .reduce((sum, p) => sum + p.amount, 0);
    }

    getDueTodayCount() {
        const today = new Date().toISOString().split('T')[0];
        return this.borrowers.filter(b => b.dueDate === today && b.payableAmount > 0).length;
    }

    getOverdueCount() {
        return this.borrowers.filter(b => this.isOverdue(b)).length;
    }

    generateCustomersTable() {
        if (this.borrowers.length === 0) {
            return `
                <div class="empty-state">
                    <div class="empty-icon">👥</div>
                    <h3>No customers found</h3>
                    <p>Add your first customer using the form above</p>
                </div>
            `;
        }

        return `
            <table class="table">
                <thead>
                    <tr>
                        <th>Customer ID</th>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>Loan Type</th>
                        <th>Loan Amount</th>
                        <th>Interest</th>
                        <th>Total Amount</th>
                        <th>Paid</th>
                        <th>Outstanding</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.borrowers.map(borrower => `
                        <tr>
                            <td><strong>#${String(borrower.id).padStart(4, '0')}</strong></td>
                            <td>
                                <strong>${borrower.name}</strong>
                                <br><small>${borrower.address || '-'}</small>
                            </td>
                            <td>${borrower.phone || '-'}</td>
                            <td>
                                <span class="interest-type">${borrower.loanType || 'Standard'}</span>
                                <br><small>${borrower.interestRate}% ${borrower.interestType}</small>
                            </td>
                            <td class="amount">₹${borrower.loanAmount.toLocaleString('en-IN')}</td>
                            <td class="amount">₹${(borrower.totalAmount - borrower.loanAmount).toLocaleString('en-IN')}</td>
                            <td class="amount">₹${borrower.totalAmount.toLocaleString('en-IN')}</td>
                            <td class="amount">₹${borrower.paidAmount.toLocaleString('en-IN')}</td>
                            <td class="amount ${borrower.payableAmount > 0 ? 'negative' : ''}">₹${borrower.payableAmount.toLocaleString('en-IN')}</td>
                            <td>
                                <span class="status-badge status-${borrower.status}">
                                    ${borrower.status}
                                </span>
                                ${this.isOverdue(borrower) ? '<br><span class="status-badge status-overdue">Overdue</span>' : ''}
                            </td>
                            <td>
                                ${borrower.payableAmount > 0 ? `<button class="action-btn btn-pay" onclick="app.quickPayment(${borrower.id})" title="Quick Payment">💸</button>` : ''}
                                <button class="action-btn btn-view" onclick="app.viewBorrower(${borrower.id})" title="View Details">👁️</button>
                                <button class="action-btn btn-edit" onclick="app.editBorrower(${borrower.id})" title="Edit">✏️</button>
                                <button class="action-btn btn-delete" onclick="app.deleteBorrower(${borrower.id})" title="Delete">🗑️</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    generatePaymentsTable() {
        if (this.payments.length === 0) {
            return `
                <div class="empty-state">
                    <div class="empty-icon">💸</div>
                    <h3>No payments recorded</h3>
                    <p>Start recording payments to see collection history</p>
                </div>
            `;
        }

        return `
            <table class="table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Customer</th>
                        <th>Amount</th>
                        <th>Method</th>
                        <th>Reference</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.payments.slice(-10).reverse().map(payment => {
                        const customer = this.borrowers.find(b => b.id === payment.customerId);
                        return `
                            <tr>
                                <td>${new Date(payment.date).toLocaleDateString('en-IN')}</td>
                                <td><strong>${customer ? customer.name : 'Unknown'}</strong></td>
                                <td class="amount">₹${payment.amount.toLocaleString('en-IN')}</td>
                                <td>
                                    <span class="interest-type">${payment.method}</span>
                                </td>
                                <td>${payment.reference || '-'}</td>
                                <td>${payment.notes || '-'}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
    }

    generateLoanSummary() {
        const loanTypes = ['daily', 'weekly', 'monthly', 'enterprise'];
        return loanTypes.map(type => {
            const loans = this.borrowers.filter(b => b.loanType === type);
            const totalLoans = loans.length;
            const disbursed = loans.reduce((sum, l) => sum + l.loanAmount, 0);
            const collected = loans.reduce((sum, l) => sum + l.paidAmount, 0);
            const outstanding = loans.reduce((sum, l) => sum + l.payableAmount, 0);
            const recovery = disbursed > 0 ? ((collected / disbursed) * 100).toFixed(1) : 0;

            return `
                <tr>
                    <td><span class="interest-type">${type.charAt(0).toUpperCase() + type.slice(1)}</span></td>
                    <td>${totalLoans}</td>
                    <td class="amount">₹${disbursed.toLocaleString('en-IN')}</td>
                    <td class="amount">₹${collected.toLocaleString('en-IN')}</td>
                    <td class="amount ${outstanding > 0 ? 'negative' : ''}">₹${outstanding.toLocaleString('en-IN')}</td>
                    <td>${recovery}%</td>
                </tr>
            `;
        }).join('');
    }

    // Event Binding Functions
    bindCustomerForm() {
        const form = document.getElementById('borrowerForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addBorrower();
            });
        }
    }

    bindPaymentForm() {
        const form = document.getElementById('paymentForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.recordPayment();
            });
        }

        // Auto-fill payment amount with outstanding amount
        const customerSelect = document.getElementById('paymentCustomer');
        const amountInput = document.getElementById('paymentAmount');
        if (customerSelect && amountInput) {
            customerSelect.addEventListener('change', (e) => {
                const customerId = parseInt(e.target.value);
                const customer = this.borrowers.find(b => b.id === customerId);
                if (customer) {
                    amountInput.value = customer.payableAmount;
                }
            });
        }
    }

    // Core Functions
    addBorrower() {
        const form = document.getElementById('borrowerForm');
        const formData = new FormData(form);
        
        const loanAmount = parseFloat(formData.get('loanAmount'));
        const interestRate = parseFloat(formData.get('interestRate'));
        const duration = parseInt(formData.get('duration')) || 6;
        
        // Calculate total amount based on interest type
        let totalAmount = loanAmount;
        const interestType = formData.get('interestType');
        
        if (interestType === 'simple') {
            totalAmount = loanAmount + (loanAmount * interestRate * duration / 100);
        } else if (interestType === 'daily') {
            totalAmount = loanAmount + (loanAmount * interestRate * duration * 30 / 100);
        }

        const borrower = {
            id: this.nextId++,
            name: formData.get('name').trim(),
            phone: formData.get('phone').trim(),
            address: formData.get('address').trim(),
            loanType: formData.get('loanType'),
            loanAmount: loanAmount,
            interestRate: interestRate,
            interestType: interestType,
            duration: duration,
            date: new Date().toLocaleDateString('en-IN'),
            totalAmount: Math.round(totalAmount),
            paidAmount: 0,
            payableAmount: Math.round(totalAmount),
            status: 'active',
            dueDate: this.calculateDueDate(duration),
            branch: this.currentBranch
        };

        // Add loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const btnText = submitBtn.querySelector('.btn-text');
        const loading = submitBtn.querySelector('.loading');
        
        btnText.style.display = 'none';
        loading.style.display = 'inline-block';
        submitBtn.disabled = true;

        // Simulate API call
        setTimeout(() => {
            this.borrowers.push(borrower);
            this.showSuccessMessage('Customer added successfully!');
            form.reset();
            
            // Update table
            document.getElementById('customersTableContainer').innerHTML = this.generateCustomersTable();
            
            // Reset button state
            btnText.style.display = 'inline';
            loading.style.display = 'none';
            submitBtn.disabled = false;
        }, 1000);
    }

    recordPayment() {
        const customerId = parseInt(document.getElementById('paymentCustomer').value);
        const amount = parseFloat(document.getElementById('paymentAmount').value);
        const date = document.getElementById('paymentDate').value;
        const method = document.getElementById('paymentMethod').value;
        const reference = document.getElementById('paymentReference').value;
        const notes = document.getElementById('paymentNotes').value;

        const borrower = this.borrowers.find(b => b.id === customerId);
        if (!borrower) {
            alert('Please select a valid customer');
            return;
        }

        if (amount <= 0 || amount > borrower.payableAmount) {
            alert(`Payment amount must be between ₹1 and ₹${borrower.payableAmount.toLocaleString('en-IN')}`);
            return;
        }

        const payment = {
            id: this.nextPaymentId++,
            customerId: customerId,
            amount: amount,
            date: date,
            method: method,
            reference: reference,
            notes: notes,
            timestamp: new Date().toISOString()
        };

        // Add loading state
        const form = document.getElementById('paymentForm');
        const submitBtn = form.querySelector('button[type="submit"]');
        const btnText = submitBtn.querySelector('.btn-text');
        const loading = submitBtn.querySelector('.loading');
        
        btnText.style.display = 'none';
        loading.style.display = 'inline-block';
        submitBtn.disabled = true;

        setTimeout(() => {
            // Update borrower record
            borrower.paidAmount += amount;
            borrower.payableAmount = Math.max(0, borrower.payableAmount - amount);
            
            if (borrower.payableAmount === 0) {
                borrower.status = 'completed';
            }

            // Add payment record
            this.payments.push(payment);
            
            this.showSuccessMessage(`Payment of ₹${amount.toLocaleString('en-IN')} recorded successfully!`);
            form.reset();
            document.getElementById('paymentDate').value = new Date().toISOString().split('T')[0];
            
            // Update customer dropdown
            const customerSelect = document.getElementById('paymentCustomer');
            customerSelect.innerHTML = `
                <option value="">Choose customer...</option>
                ${this.borrowers.filter(b => b.payableAmount > 0).map(b => 
                    `<option value="${b.id}">${b.name} (#${String(b.id).padStart(4, '0')}) - Outstanding: ₹${b.payableAmount.toLocaleString('en-IN')}</option>`
                ).join('')}
            `;

            // Update payments table
            const paymentsContainer = document.querySelector('.table-container:last-child > div');
            if (paymentsContainer) {
                paymentsContainer.innerHTML = this.generatePaymentsTable();
            }
            
            // Reset button state
            btnText.style.display = 'inline';
            loading.style.display = 'none';
            submitBtn.disabled = false;
        }, 1000);
    }

    calculateDueDate(durationMonths) {
        const dueDate = new Date();
        dueDate.setMonth(dueDate.getMonth() + durationMonths);
        return dueDate.toISOString().split('T')[0];
    }

    // Quick Payment Modal
    quickPayment(customerId) {
        this.currentCustomerId = customerId;
        const customer = this.borrowers.find(b => b.id === customerId);
        if (!customer) return;

        document.getElementById('quickPaymentAmount').value = customer.payableAmount;
        document.querySelector('#paymentModal .modal-title').textContent = `Record Payment - ${customer.name}`;
        this.showModal('paymentModal');
        
        // Bind quick payment form
        const form = document.getElementById('quickPaymentForm');
        form.onsubmit = (e) => {
            e.preventDefault();
            this.processQuickPayment();
        };
    }

    processQuickPayment() {
        const amount = parseFloat(document.getElementById('quickPaymentAmount').value);
        const method = document.getElementById('quickPaymentMethod').value;
        const notes = document.getElementById('quickPaymentNotes').value;

        const borrower = this.borrowers.find(b => b.id === this.currentCustomerId);
        if (!borrower || amount <= 0 || amount > borrower.payableAmount) {
            alert('Invalid payment amount');
            return;
        }

        const payment = {
            id: this.nextPaymentId++,
            customerId: this.currentCustomerId,
            amount: amount,
            date: new Date().toISOString().split('T')[0],
            method: method,
            reference: '',
            notes: notes,
            timestamp: new Date().toISOString()
        };

        // Update borrower
        borrower.paidAmount += amount;
        borrower.payableAmount = Math.max(0, borrower.payableAmount - amount);
        
        if (borrower.payableAmount === 0) {
            borrower.status = 'completed';
        }

        this.payments.push(payment);
        this.closeModal('paymentModal');
        this.showSuccessMessage(`Payment of ₹${amount.toLocaleString('en-IN')} recorded for ${borrower.name}!`);
        
        // Refresh current section
        this.loadSectionContent(this.currentSection);
    }

    // Modal Functions
    showModal(modalId) {
        document.getElementById(modalId).classList.add('show');
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('show');
        const form = document.querySelector(`#${modalId} form`);
        if (form) form.reset();
    }

    // Action Functions
    viewBorrower(id) {
        const borrower = this.borrowers.find(b => b.id === id);
        if (!borrower) return;

        const customerPayments = this.payments.filter(p => p.customerId === id);
        const paymentHistory = customerPayments.map(p => 
            `${new Date(p.date).toLocaleDateString('en-IN')}: ₹${p.amount.toLocaleString('en-IN')} (${p.method})`
        ).join('\n');

        alert(`Customer Details:
        
Name: ${borrower.name}
Phone: ${borrower.phone || 'Not provided'}
Address: ${borrower.address || 'Not provided'}
Loan Type: ${borrower.loanType || 'Standard'}
Loan Amount: ₹${borrower.loanAmount.toLocaleString('en-IN')}
Interest Rate: ${borrower.interestRate}% ${borrower.interestType}
Total Amount: ₹${borrower.totalAmount.toLocaleString('en-IN')}
Paid Amount: ₹${borrower.paidAmount.toLocaleString('en-IN')}
Outstanding: ₹${borrower.payableAmount.toLocaleString('en-IN')}
Status: ${borrower.status}
Due Date: ${borrower.dueDate || 'Not set'}

Payment History:
${paymentHistory || 'No payments recorded'}`);
    }

    editBorrower(id) {
        const borrower = this.borrowers.find(b => b.id === id);
        if (!borrower) return;

        const newName = prompt('Edit customer name:', borrower.name);
        if (newName && newName.trim()) {
            borrower.name = newName.trim();
            this.showSuccessMessage('Customer updated successfully!');
            this.loadSectionContent(this.currentSection);
        }
    }

    deleteBorrower(id) {
        const borrower = this.borrowers.find(b => b.id === id);
        if (!borrower) return;

        if (borrower.paidAmount > 0) {
            alert('Cannot delete customer with payment history. Please complete all transactions first.');
            return;
        }

        if (confirm(`Are you sure you want to delete ${borrower.name}?\nThis action cannot be undone.`)) {
            this.borrowers = this.borrowers.filter(b => b.id !== id);
            this.payments = this.payments.filter(p => p.customerId !== id);
            this.showSuccessMessage('Customer deleted successfully!');
            this.loadSectionContent(this.currentSection);
        }
    }

    // Report Generation
    generateReport(type) {
        switch(type) {
            case 'daily':
                this.generateDailyReport();
                break;
            case 'monthly':
                this.generateMonthlyReport();
                break;
            case 'customer':
                this.generateCustomerReport();
                break;
            case 'collection':
                this.generateCollectionReport();
                break;
        }
    }

    generateDailyReport() {
        const today = new Date().toISOString().split('T')[0];
        const todayPayments = this.payments.filter(p => p.date === today);
        const totalCollection = todayPayments.reduce((sum, p) => sum + p.amount, 0);

        alert(`Daily Report - ${new Date().toLocaleDateString('en-IN')}

Total Collections: ₹${totalCollection.toLocaleString('en-IN')}
Number of Payments: ${todayPayments.length}
Active Customers: ${this.borrowers.filter(b => b.status === 'active').length}
Due Today: ${this.getDueTodayCount()}
Overdue: ${this.getOverdueCount()}

Branch: ${this.branches[this.currentBranch]}`);
    }

    generateMonthlyReport() {
        const monthlyCollection = this.getMonthlyCollection();
        const currentMonth = new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });

        alert(`Monthly Report - ${currentMonth}

Total Collections: ₹${monthlyCollection.toLocaleString('en-IN')}
Active Loans: ${this.borrowers.filter(b => b.status === 'active').length}
Completed Loans: ${this.borrowers.filter(b => b.status === 'completed').length}
Total Outstanding: ₹${this.borrowers.reduce((sum, b) => sum + b.payableAmount, 0).toLocaleString('en-IN')}

Branch: ${this.branches[this.currentBranch]}`);
    }

    generateCustomerReport() {
        const totalCustomers = this.borrowers.length;
        const activeCustomers = this.borrowers.filter(b => b.status === 'active').length;
        const completedCustomers = this.borrowers.filter(b => b.status === 'completed').length;

        alert(`Customer Report

Total Customers: ${totalCustomers}
Active Customers: ${activeCustomers}
Completed Loans: ${completedCustomers}
Average Loan Amount: ₹${(this.borrowers.reduce((sum, b) => sum + b.loanAmount, 0) / totalCustomers || 0).toLocaleString('en-IN')}

Branch: ${this.branches[this.currentBranch]}`);
    }

    generateCollectionReport() {
        const totalCollected = this.borrowers.reduce((sum, b) => sum + b.paidAmount, 0);
        const totalDisbursed = this.borrowers.reduce((sum, b) => sum + b.loanAmount, 0);
        const recoveryRate = ((totalCollected / totalDisbursed) * 100 || 0).toFixed(2);

        alert(`Collection Report

Total Disbursed: ₹${totalDisbursed.toLocaleString('en-IN')}
Total Collected: ₹${totalCollected.toLocaleString('en-IN')}
Outstanding: ₹${this.borrowers.reduce((sum, b) => sum + b.payableAmount, 0).toLocaleString('en-IN')}
Recovery Rate: ${recoveryRate}%
Total Payments: ${this.payments.length}

Branch: ${this.branches[this.currentBranch]}`);
    }

    // Coming Soon Sections
    loadLoanTypeSection(contentArea, title, type) {
        const loansOfType = this.borrowers.filter(b => b.loanType === type);
        
        contentArea.innerHTML = `
            <div class="content-header">
                <h2 class="content-title">${title}</h2>
                <p class="content-subtitle">Manage ${type} loan collections</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-icon">📊</div>
                    <div class="stat-value">${loansOfType.length}</div>
                    <div class="stat-label">Total ${title}</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-icon">💰</div>
                    <div class="stat-value">₹${loansOfType.reduce((sum, l) => sum + l.loanAmount, 0).toLocaleString('en-IN')}</div>
                    <div class="stat-label">Amount Disbursed</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-icon">💸</div>
                    <div class="stat-value">₹${loansOfType.reduce((sum, l) => sum + l.paidAmount, 0).toLocaleString('en-IN')}</div>
                    <div class="stat-label">Collected</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-icon">⏰</div>
                    <div class="stat-value">₹${loansOfType.reduce((sum, l) => sum + l.payableAmount, 0).toLocaleString('en-IN')}</div>
                    <div class="stat-label">Outstanding</div>
                </div>
            </div>

            <div class="table-container">
                <div class="table-header">${title} - Customer List</div>
                <div>
                    ${loansOfType.length > 0 ? `
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Customer</th>
                                    <th>Loan Amount</th>
                                    <th>Paid</th>
                                    <th>Outstanding</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${loansOfType.map(loan => `
                                    <tr>
                                        <td>
                                            <strong>${loan.name}</strong>
                                            <br><small>${loan.phone}</small>
                                        </td>
                                        <td class="amount">₹${loan.loanAmount.toLocaleString('en-IN')}</td>
                                        <td class="amount">₹${loan.paidAmount.toLocaleString('en-IN')}</td>
                                        <td class="amount ${loan.payableAmount > 0 ? 'negative' : ''}">₹${loan.payableAmount.toLocaleString('en-IN')}</td>
                                        <td><span class="status-badge status-${loan.status}">${loan.status}</span></td>
                                        <td>
                                            ${loan.payableAmount > 0 ? `<button class="action-btn btn-pay" onclick="app.quickPayment(${loan.id})">💸</button>` : ''}
                                            <button class="action-btn btn-view" onclick="app.viewBorrower(${loan.id})">👁️</button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : `
                        <div class="empty-state">
                            <div class="empty-icon">📋</div>
                            <h3>No ${type} loans found</h3>
                            <p>Add customers with ${type} loan type to see them here</p>
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    loadInvestmentSection(contentArea) {
        contentArea.innerHTML = `
            <div class="content-header">
                <h2 class="content-title">Investment Management</h2>
                <p class="content-subtitle">Track your business investments</p>
            </div>
            <div class="form-container">
                <div style="text-align: center; padding: 3rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">📈</div>
                    <h3>Investment Tracking</h3>
                    <p>This feature is coming soon! Track your business investments and returns.</p>
                </div>
            </div>
        `;
    }

    loadCashoutSection(contentArea) {
        contentArea.innerHTML = `
            <div class="content-header">
                <h2 class="content-title">Cashout Management</h2>
                <p class="content-subtitle">Manage cash withdrawals and transfers</p>
            </div>
            <div class="form-container">
                <div style="text-align: center; padding: 3rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">💰</div>
                    <h3>Cashout System</h3>
                    <p>This feature is coming soon! Manage your cash flow and withdrawals.</p>
                </div>
            </div>
        `;
    }

    loadComingSoon(contentArea, section) {
        contentArea.innerHTML = `
            <div class="content-header">
                <h2 class="content-title">${section.charAt(0).toUpperCase() + section.slice(1).replace('-', ' ')}</h2>
                <p class="content-subtitle">This feature is coming soon!</p>
            </div>
            <div class="form-container">
                <div style="text-align: center; padding: 3rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">🚧</div>
                    <h3>Feature Under Development</h3>
                    <p>This section will be available in the next update.</p>
                </div>
            </div>
        `;
    }

    // Utility Functions
    showSuccessMessage(message = 'Operation completed successfully!') {
        const messageEl = document.getElementById('successMessage');
        if (messageEl) {
            messageEl.textContent = message;
            messageEl.classList.add('show');
            setTimeout(() => {
                messageEl.classList.remove('show');
            }, 3000);
        }
    }

    // Header Functions
    showNotifications() {
        const overdueCount = this.getOverdueCount();
        const dueTodayCount = this.getDueTodayCount();
        
        alert(`📢 Notifications

🚨 Overdue Loans: ${overdueCount}
⏰ Due Today: ${dueTodayCount}
📊 Active Customers: ${this.borrowers.filter(b => b.status === 'active').length}
💰 Today's Collection: ₹${this.getTodayCollection().toLocaleString('en-IN')}

Branch: ${this.branches[this.currentBranch]}`);
    }

    showSettings() {
        alert(`⚙️ Settings

Current Branch: ${this.branches[this.currentBranch]}
Total Customers: ${this.borrowers.length}
Total Payments: ${this.payments.length}
App Version: 1.0.0

Contact Support: support@vasool.com`);
    }

    logout() {
        if (confirm('Are you sure you want to logout?')) {
            alert('👋 Thank you for using Vasool! You have been logged out.');
            // In a real app, this would redirect to login page
        }
    }
}

// Initialize the app
const app = new VasoolDriveApp();

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case '1':
                e.preventDefault();
                app.switchSection('dashboard');
                break;
            case '2':
                e.preventDefault();
                app.switchSection('customer');
                break;
            case '3':
                e.preventDefault();
                app.switchSection('collection');
                break;
        }
    }
});