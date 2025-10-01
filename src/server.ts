import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import path from 'path';

import authRoutes from './routes/auth';
import userRoutes from './routes/users';
import propertyRoutes from './routes/properties';
import financialRoutes from './routes/financial';
import ticketRoutes from './routes/tickets';
import notificationRoutes from './routes/notifications';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8000;

// Trust proxy for Koyeb - MUST be first
app.set('trust proxy', true);

// Middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https:"],
      scriptSrc: ["'self'", "'unsafe-inline'", "https:"],
      imgSrc: ["'self'", "data:", "https:"],
      fontSrc: ["'self'", "https:", "data:"],
      connectSrc: ["'self'", "https:"]
    }
  }
}));
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Rate limiting - after trust proxy
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false
});
app.use(limiter);

// MongoDB connection
const MONGO_URI = process.env.MONGO_URI || process.env.MONGODB_URI || 'mongodb://localhost:27017/ph_control';

mongoose.connect(MONGO_URI)
  .then(() => console.log('✅ MongoDB conectado'))
  .catch((error) => console.error('❌ Error MongoDB:', error));

// Template engine setup (simple file serving for now)
const renderTemplate = (templatePath: string, res: express.Response) => {
  const fullPath = path.join(process.cwd(), 'templates', templatePath);
  res.sendFile(fullPath);
};

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/properties', propertyRoutes);
app.use('/api/financial', financialRoutes);
app.use('/api/tickets', ticketRoutes);
app.use('/api/notifications', notificationRoutes);

// Auth routes
app.get('/auth/login', (req, res) => renderTemplate('auth/login.html', res));
app.post('/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const response = await fetch(`${req.protocol}://${req.get('host')}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await response.json() as any;
    
    if (response.ok) {
      res.redirect('/dashboard');
    } else {
      res.redirect('/auth/login?error=' + encodeURIComponent(data.message || 'Error de login'));
    }
  } catch (error) {
    res.redirect('/auth/login?error=Error de conexión');
  }
});

app.get('/auth/register', (req, res) => renderTemplate('auth/register.html', res));
app.post('/auth/register', async (req, res) => {
  try {
    const { email, password, firstName, lastName, phone } = req.body;
    const response = await fetch(`${req.protocol}://${req.get('host')}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, firstName, lastName, phone })
    });
    const data = await response.json() as any;
    
    if (response.ok) {
      res.redirect('/auth/login?success=Usuario creado exitosamente');
    } else {
      res.redirect('/auth/register?error=' + encodeURIComponent(data.message || 'Error de registro'));
    }
  } catch (error) {
    res.redirect('/auth/register?error=Error de conexión');
  }
});

app.get('/auth/forgot-password', (req, res) => renderTemplate('auth/forgot_password.html', res));
app.get('/auth/profile', (req, res) => renderTemplate('auth/profile.html', res));

// Dashboard routes
app.get('/dashboard', (req, res) => renderTemplate('dashboard/admin.html', res));
app.get('/dashboard/resident', (req, res) => renderTemplate('dashboard/resident.html', res));

// Admin routes
app.get('/admin', (req, res) => renderTemplate('admin/dashboard.html', res));
app.get('/admin/dashboard', (req, res) => renderTemplate('admin/dashboard.html', res));
app.get('/admin/users', (req, res) => renderTemplate('admin/users.html', res));
app.get('/admin/properties', (req, res) => renderTemplate('admin/properties.html', res));
app.get('/admin/create-user', (req, res) => renderTemplate('admin/create_user.html', res));
app.get('/admin/create-property', (req, res) => renderTemplate('admin/create_property.html', res));
app.get('/admin/edit-user/:id', (req, res) => renderTemplate('admin/edit_user.html', res));
app.get('/admin/view-user/:id', (req, res) => renderTemplate('admin/view_user.html', res));
app.get('/admin/view-property/:id', (req, res) => renderTemplate('admin/view_property.html', res));

// Financial routes
app.get('/financial', (req, res) => renderTemplate('financial/index.html', res));
app.get('/financial/payments', (req, res) => renderTemplate('financial/payments.html', res));
app.get('/financial/expenses', (req, res) => renderTemplate('financial/expenses.html', res));
app.get('/financial/add-payment', (req, res) => renderTemplate('financial/add_payment.html', res));
app.get('/financial/add-expense', (req, res) => renderTemplate('financial/add_expense.html', res));
app.get('/financial/reports', (req, res) => renderTemplate('financial/reports.html', res));

// Communication routes
app.get('/communication', (req, res) => renderTemplate('communication/index.html', res));
app.get('/communication/tickets', (req, res) => renderTemplate('communication/tickets.html', res));
app.get('/communication/notifications', (req, res) => renderTemplate('communication/notifications.html', res));
app.get('/communication/create-ticket', (req, res) => renderTemplate('communication/create_ticket.html', res));
app.get('/communication/send-notification', (req, res) => renderTemplate('communication/send_notification.html', res));
app.get('/communication/view-ticket/:id', (req, res) => renderTemplate('communication/view_ticket.html', res));

// Maintenance routes
app.get('/maintenance', (req, res) => renderTemplate('maintenance/index.html', res));
app.get('/maintenance/tasks', (req, res) => renderTemplate('maintenance/tasks.html', res));
app.get('/maintenance/create-task', (req, res) => renderTemplate('maintenance/create_task.html', res));
app.get('/maintenance/schedule', (req, res) => renderTemplate('maintenance/schedule.html', res));
app.get('/maintenance/view-task/:id', (req, res) => renderTemplate('maintenance/view_task.html', res));

// Security routes
app.get('/security', (req, res) => renderTemplate('security/index.html', res));
app.get('/security/visitors', (req, res) => renderTemplate('security/visitors.html', res));
app.get('/security/incidents', (req, res) => renderTemplate('security/incidents.html', res));
app.get('/security/register-visitor', (req, res) => renderTemplate('security/register_visitor.html', res));
app.get('/security/reports', (req, res) => renderTemplate('security/reports.html', res));

// Legal routes
app.get('/legal', (req, res) => renderTemplate('legal/index.html', res));
app.get('/legal/assemblies', (req, res) => renderTemplate('legal/assemblies.html', res));
app.get('/legal/compliance', (req, res) => renderTemplate('legal/compliance.html', res));
app.get('/legal/create-assembly', (req, res) => renderTemplate('legal/create_assembly.html', res));
app.get('/legal/templates', (req, res) => renderTemplate('legal/templates.html', res));

// Documents routes
app.get('/documents', (req, res) => renderTemplate('documents/index.html', res));
app.get('/documents/upload', (req, res) => renderTemplate('documents/upload.html', res));
app.get('/documents/search', (req, res) => renderTemplate('documents/search.html', res));
app.get('/documents/categories', (req, res) => renderTemplate('documents/categories.html', res));

// Backup routes
app.get('/backup', (req, res) => renderTemplate('backup/index.html', res));
app.get('/backup/schedule', (req, res) => renderTemplate('backup/schedule.html', res));

// Audit routes
app.get('/audit', (req, res) => renderTemplate('audit/index.html', res));
app.get('/audit/logs', (req, res) => renderTemplate('audit/logs.html', res));

// Reports routes
app.get('/reports', (req, res) => renderTemplate('reports/index.html', res));

// Notifications routes
app.get('/notifications', (req, res) => renderTemplate('notifications/index.html', res));

// Landing page
app.get('/', (req, res) => {
  res.sendFile('index.html', { root: '.' });
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    mongodb: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected'
  });
});

// Serve static files (after routes to avoid conflicts)
app.use(express.static('.'));

// Error handlers
app.use((req, res) => {
  renderTemplate('errors/404.html', res);
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor en puerto ${PORT}`);
});