import express, { Request, Response } from 'express';
import Payment from '../models/Payment';
import Expense from '../models/Expense';
import Property from '../models/Property';

const router = express.Router();

// Get financial summary for properties
router.get('/summary/:propertyId?', async (req: Request, res: Response) => {
  try {
    const { propertyId } = req.params;
    const { year, month } = req.query;

    const currentYear = year ? parseInt(year as string) : new Date().getFullYear();
    const currentMonth = month ? parseInt(month as string) : new Date().getMonth() + 1;

    // Build date filter
    const startDate = new Date(currentYear, currentMonth - 1, 1);
    const endDate = new Date(currentYear, currentMonth, 1);

    let propertyFilter = {};
    if (propertyId) {
      propertyFilter = { propertyId };
    }

    // Get payments
    const payments = await Payment.find({
      paymentDate: { $gte: startDate, $lt: endDate },
      status: 'paid',
      ...propertyFilter
    }).populate('unitId', 'number propertyId');

    // Get expenses
    const expenses = await Expense.find({
      expenseDate: { $gte: startDate, $lt: endDate },
      status: 'paid',
      ...propertyFilter
    });

    const totalIncome = payments.reduce((sum, payment) => sum + payment.amount, 0);
    const totalExpenses = expenses.reduce((sum, expense) => sum + expense.amount, 0);
    const netIncome = totalIncome - totalExpenses;

    res.json({
      period: { year: currentYear, month: currentMonth },
      summary: {
        totalIncome,
        totalExpenses,
        netIncome
      },
      transactions: {
        payments: payments.slice(0, 10), // Last 10 payments
        expenses: expenses.slice(0, 10)  // Last 10 expenses
      }
    });
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Get payments
router.get('/payments', async (req: Request, res: Response) => {
  try {
    const { propertyId, status, page = 1, limit = 20 } = req.query;

    let filter: any = {};
    if (propertyId) filter['unitId.propertyId'] = propertyId;
    if (status) filter.status = status;

    const payments = await Payment.find(filter)
      .populate('unitId', 'number propertyId')
      .populate('userId', 'firstName lastName email')
      .sort({ paymentDate: -1 })
      .limit(parseInt(limit as string))
      .skip((parseInt(page as string) - 1) * parseInt(limit as string));

    const total = await Payment.countDocuments(filter);

    res.json({
      payments,
      pagination: {
        page: parseInt(page as string),
        limit: parseInt(limit as string),
        total,
        pages: Math.ceil(total / parseInt(limit as string))
      }
    });
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Get expenses
router.get('/expenses', async (req: Request, res: Response) => {
  try {
    const { propertyId, category, page = 1, limit = 20 } = req.query;

    let filter: any = {};
    if (propertyId) filter.propertyId = propertyId;
    if (category) filter.category = category;

    const expenses = await Expense.find(filter)
      .populate('propertyId', 'name code')
      .populate('createdBy', 'firstName lastName')
      .sort({ expenseDate: -1 })
      .limit(parseInt(limit as string))
      .skip((parseInt(page as string) - 1) * parseInt(limit as string));

    const total = await Expense.countDocuments(filter);

    res.json({
      expenses,
      pagination: {
        page: parseInt(page as string),
        limit: parseInt(limit as string),
        total,
        pages: Math.ceil(total / parseInt(limit as string))
      }
    });
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

export default router;