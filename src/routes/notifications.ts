import express, { Request, Response } from 'express';
import Notification from '../models/Notification';

const router = express.Router();

// Get notifications for user
router.get('/', async (req: Request, res: Response) => {
  try {
    const { userId, unreadOnly = 'false', limit = 20 } = req.query;

    let filter: any = { userId };
    if (unreadOnly === 'true') {
      filter.isRead = false;
    }

    // Filter out expired notifications
    const now = new Date();
    filter.$or = [
      { expiresAt: { $exists: false } },
      { expiresAt: null },
      { expiresAt: { $gt: now } }
    ];

    const notifications = await Notification.find(filter)
      .sort({ createdAt: -1 })
      .limit(parseInt(limit as string));

    res.json({
      notifications: notifications.map(n => ({
        id: n._id,
        title: n.title,
        message: n.message,
        type: n.notificationType,
        priority: n.priority,
        actionUrl: n.actionUrl,
        createdAt: n.createdAt,
        isRead: n.isRead
      })),
      unreadCount: notifications.filter(n => !n.isRead).length
    });
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Get unread count
router.get('/unread-count', async (req: Request, res: Response) => {
  try {
    const { userId } = req.query;

    const count = await Notification.countDocuments({
      userId,
      isRead: false,
      $or: [
        { expiresAt: { $exists: false } },
        { expiresAt: null },
        { expiresAt: { $gt: new Date() } }
      ]
    });

    res.json({ count });
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Mark notification as read
router.post('/:id/read', async (req: Request, res: Response) => {
  try {
    const notification = await Notification.findByIdAndUpdate(
      req.params.id,
      {
        isRead: true,
        readAt: new Date()
      },
      { new: true }
    );

    if (!notification) {
      return res.status(404).json({ message: 'Notificación no encontrada' });
    }

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Mark all notifications as read
router.post('/mark-all-read', async (req: Request, res: Response) => {
  try {
    const { userId } = req.body;

    const result = await Notification.updateMany(
      { userId, isRead: false },
      {
        isRead: true,
        readAt: new Date()
      }
    );

    res.json({ success: true, count: result.modifiedCount });
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

// Create notification
router.post('/', async (req: Request, res: Response) => {
  try {
    const { userId, title, message, type, priority, actionUrl } = req.body;

    const notification = new Notification({
      userId,
      title,
      message,
      notificationType: type || 'info',
      priority: priority || 'normal',
      actionUrl
    });

    await notification.save();

    res.status(201).json(notification);
  } catch (error) {
    res.status(500).json({ message: 'Error del servidor' });
  }
});

export default router;