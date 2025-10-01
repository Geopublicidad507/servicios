import express, { Request, Response } from 'express';
import Property from '../models/Property';
import Unit from '../models/Unit';

const router = express.Router();

// Get all properties
router.get('/', async (req: Request, res: Response) => {
  try {
    const properties = await Property.find({ isActive: true })
      .populate('adminId', 'firstName lastName email')
      .sort({ createdAt: -1 });

    res.json(properties);
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Get property by ID
router.get('/:id', async (req: Request, res: Response) => {
  try {
    const property = await Property.findById(req.params.id)
      .populate('adminId', 'firstName lastName email');

    if (!property) {
      return res.status(404).json({ message: 'Propiedad no encontrada' });
    }

    res.json(property);
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Get units for a property
router.get('/:id/units', async (req: Request, res: Response) => {
  try {
    const units = await Unit.find({ propertyId: req.params.id })
      .populate('ownerId', 'firstName lastName email')
      .sort({ number: 1 });

    res.json(units);
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

export default router;