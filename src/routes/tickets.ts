import express, { Request, Response } from 'express';
import Ticket from '../models/Ticket';

const router = express.Router();

// Get all tickets
router.get('/', async (req: Request, res: Response) => {
  try {
    const { status, category, page = 1, limit = 20 } = req.query;

    let filter: any = {};
    if (status) filter.status = status;
    if (category) filter.category = category;

    const tickets = await Ticket.find(filter)
      .populate('userId', 'firstName lastName email')
      .populate('assignedTo', 'firstName lastName email')
      .sort({ createdAt: -1 })
      .limit(parseInt(limit as string))
      .skip((parseInt(page as string) - 1) * parseInt(limit as string));

    const total = await Ticket.countDocuments(filter);

    res.json({
      tickets,
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

// Get ticket by ID
router.get('/:id', async (req: Request, res: Response) => {
  try {
    const ticket = await Ticket.findById(req.params.id)
      .populate('userId', 'firstName lastName email')
      .populate('assignedTo', 'firstName lastName email');

    if (!ticket) {
      return res.status(404).json({ message: 'Ticket no encontrado' });
    }

    res.json(ticket);
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Create new ticket
router.post('/', async (req: Request, res: Response) => {
  try {
    const { title, description, category, priority } = req.body;

    const ticket = new Ticket({
      userId: req.body.userId, // This should come from JWT token in real app
      title,
      description,
      category,
      priority: priority || 'medium'
    });

    await ticket.save();
    await ticket.populate('userId', 'firstName lastName email');

    res.status(201).json(ticket);
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Update ticket
router.put('/:id', async (req: Request, res: Response) => {
  try {
    const { status, assignedTo, resolution } = req.body;

    const ticket = await Ticket.findByIdAndUpdate(
      req.params.id,
      {
        status,
        assignedTo,
        resolution,
        updatedAt: new Date()
      },
      { new: true }
    ).populate('userId', 'firstName lastName email')
     .populate('assignedTo', 'firstName lastName email');

    if (!ticket) {
      return res.status(404).json({ message: 'Ticket no encontrado' });
    }

    res.json(ticket);
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

export default router;