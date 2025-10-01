import mongoose, { Document, Schema } from 'mongoose';

export interface IProperty extends Document {
  name: string;
  code: string;
  address: string;
  totalUnits: number;
  adminId: mongoose.Types.ObjectId;
  monthlyFee: number;
  createdAt: Date;
  isActive: boolean;
}

const PropertySchema = new Schema<IProperty>({
  name: { type: String, required: true, maxlength: 200 },
  code: { type: String, required: true, unique: true, maxlength: 20 },
  address: { type: String, required: true },
  totalUnits: { type: Number, required: true, min: 1 },
  adminId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  monthlyFee: { type: Number, default: 0.00 },
  createdAt: { type: Date, default: Date.now },
  isActive: { type: Boolean, default: true }
});

export default mongoose.model<IProperty>('Property', PropertySchema);