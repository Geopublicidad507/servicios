import mongoose, { Document, Schema } from 'mongoose';

export interface IUnit extends Document {
  number: string;
  propertyId: mongoose.Types.ObjectId;
  ownerId?: mongoose.Types.ObjectId;
  unitType: 'apartment' | 'parking' | 'storage';
  area?: number;
  monthlyFee: number;
  isOccupied: boolean;
  createdAt: Date;
}

const UnitSchema = new Schema<IUnit>({
  number: { type: String, required: true, maxlength: 20 },
  propertyId: { type: Schema.Types.ObjectId, ref: 'Property', required: true },
  ownerId: { type: Schema.Types.ObjectId, ref: 'User' },
  unitType: {
    type: String,
    enum: ['apartment', 'parking', 'storage'],
    default: 'apartment'
  },
  area: { type: Number },
  monthlyFee: { type: Number, default: 0.00 },
  isOccupied: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now }
});

export default mongoose.model<IUnit>('Unit', UnitSchema);