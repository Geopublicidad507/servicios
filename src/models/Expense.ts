import mongoose, { Document, Schema } from 'mongoose';

export interface IExpense extends Document {
  propertyId: mongoose.Types.ObjectId;
  category: 'maintenance' | 'cleaning' | 'security' | 'utilities' | 'other';
  description: string;
  amount: number;
  expenseDate: Date;
  vendor?: string;
  invoiceNumber?: string;
  paymentMethod: string;
  status: 'paid' | 'pending' | 'approved';
  createdBy?: mongoose.Types.ObjectId;
  createdAt: Date;
}

const ExpenseSchema = new Schema<IExpense>({
  propertyId: { type: Schema.Types.ObjectId, ref: 'Property', required: true },
  category: {
    type: String,
    enum: ['maintenance', 'cleaning', 'security', 'utilities', 'other'],
    required: true
  },
  description: { type: String, required: true },
  amount: { type: Number, required: true },
  expenseDate: { type: Date, required: true },
  vendor: { type: String, maxlength: 200 },
  invoiceNumber: { type: String, maxlength: 100 },
  paymentMethod: { type: String, default: 'cash' },
  status: {
    type: String,
    enum: ['paid', 'pending', 'approved'],
    default: 'paid'
  },
  createdBy: { type: Schema.Types.ObjectId, ref: 'User' },
  createdAt: { type: Date, default: Date.now }
});

export default mongoose.model<IExpense>('Expense', ExpenseSchema);