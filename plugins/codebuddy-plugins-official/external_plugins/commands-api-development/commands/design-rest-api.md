---
description: Design RESTful API architecture
category: api-development
---

# Design REST API

Design RESTful API architecture

## Instructions

1. **API Design Strategy and Planning**
   - Analyze business requirements and define API scope
   - Identify resources, entities, and their relationships
   - Plan API versioning strategy and backward compatibility
   - Define authentication and authorization requirements
   - Plan for scalability, rate limiting, and performance

2. **RESTful Resource Design**
   - Design RESTful endpoints following REST principles:

   **Express.js API Structure:**
   ```javascript
   // routes/api/v1/index.js
   const express = require('express');
   const router = express.Router();

   // Resource-based routing structure
   const userRoutes = require('./users');
   const productRoutes = require('./products');
   const orderRoutes = require('./orders');
   const authRoutes = require('./auth');

   // API versioning and middleware
   router.use('/auth', authRoutes);
   router.use('/users', userRoutes);
   router.use('/products', productRoutes);
   router.use('/orders', orderRoutes);

   module.exports = router;

   // routes/api/v1/users.js
   const express = require('express');
   const router = express.Router();
   const { validateRequest, authenticate, authorize } = require('../../../middleware');
   const userController = require('../../../controllers/userController');
   const userValidation = require('../../../validations/userValidation');

   // User resource endpoints
   router.get('/', 
     authenticate,
     authorize(['admin', 'manager']),
     validateRequest(userValidation.listUsers),
     userController.listUsers
   );

   router.get('/:id', 
     authenticate,
     validateRequest(userValidation.getUser),
     userController.getUser
   );

   router.post('/',
     authenticate,
     authorize(['admin']),
     validateRequest(userValidation.createUser),
     userController.createUser
   );

   router.put('/:id',
     authenticate,
     validateRequest(userValidation.updateUser),
     userController.updateUser
   );

   router.patch('/:id',
     authenticate,
     validateRequest(userValidation.patchUser),
     userController.patchUser
   );

   router.delete('/:id',
     authenticate,
     authorize(['admin']),
     validateRequest(userValidation.deleteUser),
     userController.deleteUser
   );

   // Nested resource endpoints
   router.get('/:id/orders',
     authenticate,
     validateRequest(userValidation.getUserOrders),
     userController.getUserOrders
   );

   router.get('/:id/profile',
     authenticate,
     validateRequest(userValidation.getUserProfile),
     userController.getUserProfile
   );

   module.exports = router;
   ```

3. **Request/Response Data Models**
   - Define comprehensive data models and validation:

   **Data Validation with Joi:**
   ```javascript
   // validations/userValidation.js
   const Joi = require('joi');

   const userSchema = {
     create: Joi.object({
       email: Joi.string().email().required(),
       password: Joi.string().min(8).pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/).required(),
       firstName: Joi.string().trim().min(1).max(100).required(),
       lastName: Joi.string().trim().min(1).max(100).required(),
       phone: Joi.string().pattern(/^\+?[\d\s\-\(\)]{10,20}$/).optional(),
       dateOfBirth: Joi.date().max('now').optional(),
       role: Joi.string().valid('user', 'admin', 'manager').default('user')
     }),

     update: Joi.object({
       email: Joi.string().email().optional(),
       firstName: Joi.string().trim().min(1).max(100).optional(),
       lastName: Joi.string().trim().min(1).max(100).optional(),
       phone: Joi.string().pattern(/^\+?[\d\s\-\(\)]{10,20}$/).optional(),
       dateOfBirth: Joi.date().max('now').optional(),
       status: Joi.string().valid('active', 'inactive', 'suspended').optional()
     }),

     list: Joi.object({
       page: Joi.number().integer().min(1).default(1),
       limit: Joi.number().integer().min(1).max(100).default(20),
       sort: Joi.string().valid('id', 'email', 'firstName', 'lastName', 'createdAt').default('id'),
       order: Joi.string().valid('asc', 'desc').default('asc'),
       search: Joi.string().trim().min(1).optional(),
       status: Joi.string().valid('active', 'inactive', 'suspended').optional(),
       role: Joi.string().valid('user', 'admin', 'manager').optional()
     }),

     params: Joi.object({
       id: Joi.number().integer().positive().required()
     })
   };

   const validateRequest = (schema) => {
     return (req, res, next) => {
       const validationTargets = {
         body: req.body,
         query: req.query,
         params: req.params
       };

       const errors = {};

       // Validate each part of the request
       Object.keys(schema).forEach(target => {
         const { error, value } = schema[target].validate(validationTargets[target], {
           abortEarly: false,
           allowUnknown: false,
           stripUnknown: true
         });

         if (error) {
           errors[target] = error.details.map(detail => ({
             field: detail.path.join('.'),
             message: detail.message,
             value: detail.context.value
           }));
         } else {
           req[target] = value;
         }
       });

       if (Object.keys(errors).length > 0) {
         return res.status(400).json({
           error: 'Validation failed',
           details: errors,
           timestamp: new Date().toISOString()
         });
       }

       next();
     };
   };

   module.exports = {
     listUsers: validateRequest({ query: userSchema.list }),
     getUser: validateRequest({ params: userSchema.params }),
     createUser: validateRequest({ body: userSchema.create }),
     updateUser: validateRequest({ 
       params: userSchema.params, 
       body: userSchema.update 
     }),
     patchUser: validateRequest({ 
       params: userSchema.params, 
       body: userSchema.update 
     }),
     deleteUser: validateRequest({ params: userSchema.params }),
     getUserOrders: validateRequest({ 
       params: userSchema.params,
       query: Joi.object({
         page: Joi.number().integer().min(1).default(1),
         limit: Joi.number().integer().min(1).max(50).default(10),
         status: Joi.string().valid('pending', 'processing', 'shipped', 'delivered', 'cancelled').optional()
       })
     })
   };
   ```

4. **Controller Implementation**
   - Implement robust controller logic:

   **User Controller Example:**
   ```javascript
   // controllers/userController.js
   const userService = require('../services/userService');
   const { ApiError, ApiResponse } = require('../utils/apiResponse');

   class UserController {
     async listUsers(req, res, next) {
       try {
         const { page, limit, sort, order, search, status, role } = req.query;
         
         const filters = {};
         if (search) filters.search = search;
         if (status) filters.status = status;
         if (role) filters.role = role;

         const result = await userService.findUsers({
           page,
           limit,
           sort,
           order,
           filters
         });

         res.json(new ApiResponse('success', 'Users retrieved successfully', {
           users: result.users,
           pagination: {
             page: result.page,
             limit: result.limit,
             total: result.total,
             totalPages: result.totalPages,
             hasNext: result.hasNext,
             hasPrev: result.hasPrev
           }
         }));
       } catch (error) {
         next(error);
       }
     }

     async getUser(req, res, next) {
       try {
         const { id } = req.params;
         const requestingUserId = req.user.id;
         const requestingUserRole = req.user.role;

         // Authorization check
         if (id !== requestingUserId && !['admin', 'manager'].includes(requestingUserRole)) {
           throw new ApiError(403, 'Insufficient permissions to access this user');
         }

         const user = await userService.findById(id);
         if (!user) {
           throw new ApiError(404, 'User not found');
         }

         // Filter sensitive data based on permissions
         const filteredUser = userService.filterUserData(user, requestingUserRole, requestingUserId);

         res.json(new ApiResponse('success', 'User retrieved successfully', { user: filteredUser }));
       } catch (error) {
         next(error);
       }
     }

     async createUser(req, res, next) {
       try {
         const userData = req.body;
         
         // Check for existing user
         const existingUser = await userService.findByEmail(userData.email);
         if (existingUser) {
           throw new ApiError(409, 'User with this email already exists');
         }

         const newUser = await userService.createUser(userData);
         
         // Remove sensitive data from response
         const responseUser = userService.filterUserData(newUser, 'admin');

         res.status(201).json(new ApiResponse(
           'success', 
           'User created successfully', 
           { user: responseUser }
         ));
       } catch (error) {
         next(error);
       }
     }

     async updateUser(req, res, next) {
       try {
         const { id } = req.params;
         const updateData = req.body;
         const requestingUserId = req.user.id;
         const requestingUserRole = req.user.role;

         // Authorization check
         if (id !== requestingUserId && !['admin', 'manager'].includes(requestingUserRole)) {
           throw new ApiError(403, 'Insufficient permissions to update this user');
         }

         // Restrict certain fields based on role
         if (updateData.role && !['admin'].includes(requestingUserRole)) {
           throw new ApiError(403, 'Insufficient permissions to update user role');
         }

         const existingUser = await userService.findById(id);
         if (!existingUser) {
           throw new ApiError(404, 'User not found');
         }

         const updatedUser = await userService.updateUser(id, updateData);
         const filteredUser = userService.filterUserData(updatedUser, requestingUserRole, requestingUserId);

         res.json(new ApiResponse('success', 'User updated successfully', { user: filteredUser }));
       } catch (error) {
         next(error);
       }
     }

     async deleteUser(req, res, next) {
       try {
         const { id } = req.params;
         const requestingUserId = req.user.id;

         // Prevent self-deletion
         if (id === requestingUserId) {
           throw new ApiError(400, 'Cannot delete your own account');
         }

         const existingUser = await userService.findById(id);
         if (!existingUser) {
           throw new ApiError(404, 'User not found');
         }

         await userService.deleteUser(id);

         res.status(204).send();
       } catch (error) {
         next(error);
       }
     }

     async getUserOrders(req, res, next) {
       try {
         const { id } = req.params;
         const { page, limit, status } = req.query;
         const requestingUserId = req.user.id;
         const requestingUserRole = req.user.role;

         // Authorization check
         if (id !== requestingUserId && !['admin', 'manager'].includes(requestingUserRole)) {
           throw new ApiError(403, 'Insufficient permissions to access user orders');
         }

         const orders = await userService.getUserOrders(id, {
           page,
           limit,
           status
         });

         res.json(new ApiResponse('success', 'User orders retrieved successfully', orders));
       } catch (error) {
         next(error);
       }
     }
   }

   module.exports = new UserController();
   ```

5. **API Response Standardization**
   - Implement consistent response formats:

   **API Response Utilities:**
   ```javascript
   // utils/apiResponse.js
   class ApiResponse {
     constructor(status, message, data = null, meta = null) {
       this.status = status;
       this.message = message;
       this.timestamp = new Date().toISOString();
       
       if (data !== null) {
         this.data = data;
       }
       
       if (meta !== null) {
         this.meta = meta;
       }
     }

     static success(message, data = null, meta = null) {
       return new ApiResponse('success', message, data, meta);
     }

     static error(message, errors = null) {
       const response = new ApiResponse('error', message);
       if (errors) {
         response.errors = errors;
       }
       return response;
     }

     static paginated(message, data, pagination) {
       return new ApiResponse('success', message, data, { pagination });
     }
   }

   class ApiError extends Error {
     constructor(statusCode, message, errors = null, isOperational = true, stack = '') {
       super(message);
       this.statusCode = statusCode;
       this.isOperational = isOperational;
       this.errors = errors;
       
       if (stack) {
         this.stack = stack;
       } else {
         Error.captureStackTrace(this, this.constructor);
       }
     }

     static badRequest(message, errors = null) {
       return new ApiError(400, message, errors);
     }

     static unauthorized(message = 'Unauthorized access') {
       return new ApiError(401, message);
     }

     static forbidden(message = 'Forbidden access') {
       return new ApiError(403, message);
     }

     static notFound(message = 'Resource not found') {
       return new ApiError(404, message);
     }

     static conflict(message, errors = null) {
       return new ApiError(409, message, errors);
     }

     static validationError(message, errors) {
       return new ApiError(422, message, errors);
     }

     static internalError(message = 'Internal server error') {
       return new ApiError(500, message);
     }
   }

   // Error handling middleware
   const errorHandler = (error, req, res, next) => {
     let { statusCode, message, errors } = error;

     if (!error.isOperational) {
       statusCode = 500;
       message = 'Internal server error';
       
       // Log unexpected errors
       console.error('Unexpected error:', error);
     }

     const response = ApiResponse.error(message, errors);
     
     // Add request ID for tracking
     if (req.requestId) {
       response.requestId = req.requestId;
     }

     // Add stack trace in development
     if (process.env.NODE_ENV === 'development') {
       response.stack = error.stack;
     }

     res.status(statusCode).json(response);
   };

   // 404 handler
   const notFoundHandler = (req, res) => {
     const error = ApiError.notFound(`Route ${req.originalUrl} not found`);
     res.status(404).json(ApiResponse.error(error.message));
   };

   module.exports = {
     ApiResponse,
     ApiError,
     errorHandler,
     notFoundHandler
   };
   ```

6. **Authentication and Authorization**
   - Implement comprehensive auth system:

   **JWT Authentication Middleware:**
   ```javascript
   // middleware/auth.js
   const jwt = require('jsonwebtoken');
   const { ApiError } = require('../utils/apiResponse');
   const userService = require('../services/userService');

   class AuthMiddleware {
     static async authenticate(req, res, next) {
       try {
         const authHeader = req.headers.authorization;
         
         if (!authHeader) {
           throw ApiError.unauthorized('Access token is required');
         }

         const token = authHeader.startsWith('Bearer ') 
           ? authHeader.slice(7) 
           : authHeader;

         if (!token) {
           throw ApiError.unauthorized('Invalid authorization header format');
         }

         let decoded;
         try {
           decoded = jwt.verify(token, process.env.JWT_SECRET);
         } catch (jwtError) {
           if (jwtError.name === 'TokenExpiredError') {
             throw ApiError.unauthorized('Access token has expired');
           } else if (jwtError.name === 'JsonWebTokenError') {
             throw ApiError.unauthorized('Invalid access token');
           } else {
             throw ApiError.unauthorized('Token verification failed');
           }
         }

         // Fetch user and verify account status
         const user = await userService.findById(decoded.userId);
         if (!user) {
           throw ApiError.unauthorized('User not found');
         }

         if (user.status !== 'active') {
           throw ApiError.unauthorized('Account is not active');
         }

         // Check if token is still valid (not invalidated)
         if (user.tokenVersion && decoded.tokenVersion !== user.tokenVersion) {
           throw ApiError.unauthorized('Token has been invalidated');
         }

         // Attach user to request
         req.user = {
           id: user.id,
           email: user.email,
           role: user.role,
           permissions: user.permissions || []
         };

         next();
       } catch (error) {
         next(error);
       }
     }

     static authorize(requiredRoles = [], requiredPermissions = []) {
       return (req, res, next) => {
         try {
           if (!req.user) {
             throw ApiError.unauthorized('Authentication required');
           }

           // Check role-based authorization
           if (requiredRoles.length > 0) {
             const hasRequiredRole = requiredRoles.includes(req.user.role);
             if (!hasRequiredRole) {
               throw ApiError.forbidden(`Requires one of the following roles: ${requiredRoles.join(', ')}`);
             }
           }

           // Check permission-based authorization
           if (requiredPermissions.length > 0) {
             const userPermissions = req.user.permissions || [];
             const hasRequiredPermission = requiredPermissions.some(permission => 
               userPermissions.includes(permission)
             );
             
             if (!hasRequiredPermission) {
               throw ApiError.forbidden(`Requires one of the following permissions: ${requiredPermissions.join(', ')}`);
             }
           }

           next();
         } catch (error) {
           next(error);
         }
       };
     }

     static async rateLimitByUser(req, res, next) {
       try {
         if (!req.user) {
           return next();
         }

         const userId = req.user.id;
         const key = `rate_limit:${userId}:${req.route.path}`;
         
         // Implement rate limiting logic here
         // This is a simplified example
         const requestCount = await redis.incr(key);
         if (requestCount === 1) {
           await redis.expire(key, 3600); // 1 hour window
         }

         const limit = req.user.role === 'admin' ? 1000 : 100; // Different limits by role
         
         if (requestCount > limit) {
           throw ApiError.tooManyRequests('Rate limit exceeded');
         }

         res.set({
           'X-RateLimit-Limit': limit,
           'X-RateLimit-Remaining': Math.max(0, limit - requestCount),
           'X-RateLimit-Reset': new Date(Date.now() + 3600000).toISOString()
         });

         next();
       } catch (error) {
         next(error);
       }
     }
   }

   module.exports = AuthMiddleware;
   ```

7. **API Documentation with OpenAPI/Swagger**
   - Generate comprehensive API documentation:

   **Swagger Configuration:**
   ```javascript
   // swagger/swagger.js
   const swaggerJsdoc = require('swagger-jsdoc');
   const swaggerUi = require('swagger-ui-express');

   const options = {
     definition: {
       openapi: '3.0.0',
       info: {
         title: 'REST API',
         version: '1.0.0',
         description: 'A comprehensive REST API with authentication and authorization',
         contact: {
           name: 'API Support',
           email: 'api-support@example.com'
         },
         license: {
           name: 'MIT',
           url: 'https://opensource.org/licenses/MIT'
         }
       },
       servers: [
         {
           url: process.env.API_URL || 'http://localhost:3000',
           description: 'Development server'
         },
         {
           url: 'https://api.example.com',
           description: 'Production server'
         }
       ],
       components: {
         securitySchemes: {
           bearerAuth: {
             type: 'http',
             scheme: 'bearer',
             bearerFormat: 'JWT',
             description: 'JWT Authorization header using the Bearer scheme'
           }
         },
         schemas: {
           User: {
             type: 'object',
             required: ['email', 'firstName', 'lastName'],
             properties: {
               id: {
                 type: 'integer',
                 description: 'Unique user identifier',
                 example: 1
               },
               email: {
                 type: 'string',
                 format: 'email',
                 description: 'User email address',
                 example: 'user@example.com'
               },
               firstName: {
                 type: 'string',
                 description: 'User first name',
                 example: 'John'
               },
               lastName: {
                 type: 'string',
                 description: 'User last name',
                 example: 'Doe'
               },
               role: {
                 type: 'string',
                 enum: ['user', 'admin', 'manager'],
                 description: 'User role',
                 example: 'user'
               },
               status: {
                 type: 'string',
                 enum: ['active', 'inactive', 'suspended'],
                 description: 'Account status',
                 example: 'active'
               },
               createdAt: {
                 type: 'string',
                 format: 'date-time',
                 description: 'Account creation timestamp'
               },
               updatedAt: {
                 type: 'string',
                 format: 'date-time',
                 description: 'Last update timestamp'
               }
             }
           },
           ApiResponse: {
             type: 'object',
             properties: {
               status: {
                 type: 'string',
                 enum: ['success', 'error'],
                 example: 'success'
               },
               message: {
                 type: 'string',
                 example: 'Operation completed successfully'
               },
               timestamp: {
                 type: 'string',
                 format: 'date-time',
                 example: '2024-01-15T10:30:00Z'
               },
               data: {
                 type: 'object',
                 description: 'Response data (varies by endpoint)'
               }
             }
           },
           ErrorResponse: {
             type: 'object',
             properties: {
               status: {
                 type: 'string',
                 enum: ['error'],
                 example: 'error'
               },
               message: {
                 type: 'string',
                 example: 'An error occurred'
               },
               timestamp: {
                 type: 'string',
                 format: 'date-time'
               },
               errors: {
                 type: 'object',
                 description: 'Detailed error information'
               }
             }
           },
           PaginationMeta: {
             type: 'object',
             properties: {
               pagination: {
                 type: 'object',
                 properties: {
                   page: { type: 'integer', example: 1 },
                   limit: { type: 'integer', example: 20 },
                   total: { type: 'integer', example: 100 },
                   totalPages: { type: 'integer', example: 5 },
                   hasNext: { type: 'boolean', example: true },
                   hasPrev: { type: 'boolean', example: false }
                 }
               }
             }
           }
         },
         responses: {
           UnauthorizedError: {
             description: 'Access token is missing or invalid',
             content: {
               'application/json': {
                 schema: { $ref: '#/components/schemas/ErrorResponse' }
               }
             }
           },
           ForbiddenError: {
             description: 'Insufficient permissions',
             content: {
               'application/json': {
                 schema: { $ref: '#/components/schemas/ErrorResponse' }
               }
             }
           },
           NotFoundError: {
             description: 'Resource not found',
             content: {
               'application/json': {
                 schema: { $ref: '#/components/schemas/ErrorResponse' }
               }
             }
           },
           ValidationError: {
             description: 'Request validation failed',
             content: {
               'application/json': {
                 schema: { $ref: '#/components/schemas/ErrorResponse' }
               }
             }
           }
         }
       },
       security: [
         {
           bearerAuth: []
         }
       ]
     },
     apis: ['./routes/**/*.js', './controllers/**/*.js']
   };

   const specs = swaggerJsdoc(options);

   const swaggerOptions = {
     explorer: true,
     swaggerOptions: {
       docExpansion: 'none',
       filter: true,
       showRequestDuration: true
     }
   };

   module.exports = {
     serve: swaggerUi.serve,
     setup: swaggerUi.setup(specs, swaggerOptions),
     specs
   };
   ```

   **Controller Documentation:**
   ```javascript
   // Add to userController.js
   /**
    * @swagger
    * /api/v1/users:
    *   get:
    *     summary: List all users
    *     tags: [Users]
    *     security:
    *       - bearerAuth: []
    *     parameters:
    *       - in: query
    *         name: page
    *         schema:
    *           type: integer
    *           minimum: 1
    *           default: 1
    *         description: Page number
    *       - in: query
    *         name: limit
    *         schema:
    *           type: integer
    *           minimum: 1
    *           maximum: 100
    *           default: 20
    *         description: Number of users per page
    *       - in: query
    *         name: search
    *         schema:
    *           type: string
    *         description: Search term for user names or email
    *       - in: query
    *         name: status
    *         schema:
    *           type: string
    *           enum: [active, inactive, suspended]
    *         description: Filter by user status
    *     responses:
    *       200:
    *         description: Users retrieved successfully
    *         content:
    *           application/json:
    *             schema:
    *               allOf:
    *                 - $ref: '#/components/schemas/ApiResponse'
    *                 - type: object
    *                   properties:
    *                     data:
    *                       type: object
    *                       properties:
    *                         users:
    *                           type: array
    *                           items:
    *                             $ref: '#/components/schemas/User'
    *                     meta:
    *                       $ref: '#/components/schemas/PaginationMeta'
    *       401:
    *         $ref: '#/components/responses/UnauthorizedError'
    *       403:
    *         $ref: '#/components/responses/ForbiddenError'
    *
    *   post:
    *     summary: Create a new user
    *     tags: [Users]
    *     security:
    *       - bearerAuth: []
    *     requestBody:
    *       required: true
    *       content:
    *         application/json:
    *           schema:
    *             type: object
    *             required:
    *               - email
    *               - password
    *               - firstName
    *               - lastName
    *             properties:
    *               email:
    *                 type: string
    *                 format: email
    *               password:
    *                 type: string
    *                 minLength: 8
    *               firstName:
    *                 type: string
    *                 minLength: 1
    *                 maxLength: 100
    *               lastName:
    *                 type: string
    *                 minLength: 1
    *                 maxLength: 100
    *               phone:
    *                 type: string
    *               role:
    *                 type: string
    *                 enum: [user, admin, manager]
    *     responses:
    *       201:
    *         description: User created successfully
    *         content:
    *           application/json:
    *             schema:
    *               allOf:
    *                 - $ref: '#/components/schemas/ApiResponse'
    *                 - type: object
    *                   properties:
    *                     data:
    *                       type: object
    *                       properties:
    *                         user:
    *                           $ref: '#/components/schemas/User'
    *       400:
    *         $ref: '#/components/responses/ValidationError'
    *       409:
    *         description: User with email already exists
    */
   ```

8. **API Testing and Quality Assurance**
   - Implement comprehensive API testing:

   **API Test Suite:**
   ```javascript
   // tests/api/users.test.js
   const request = require('supertest');
   const app = require('../../app');
   const { setupTestDb, teardownTestDb, createTestUser, getAuthToken } = require('../helpers/testHelpers');

   describe('Users API', () => {
     let authToken;
     let testUser;

     beforeAll(async () => {
       await setupTestDb();
       testUser = await createTestUser({ role: 'admin' });
       authToken = await getAuthToken(testUser);
     });

     afterAll(async () => {
       await teardownTestDb();
     });

     describe('GET /api/v1/users', () => {
       test('should return paginated users list for admin', async () => {
         const response = await request(app)
           .get('/api/v1/users')
           .set('Authorization', `Bearer ${authToken}`)
           .expect(200);

         expect(response.body).toMatchObject({
           status: 'success',
           message: 'Users retrieved successfully',
           data: {
             users: expect.any(Array)
           },
           meta: {
             pagination: {
               page: 1,
               limit: 20,
               total: expect.any(Number),
               totalPages: expect.any(Number),
               hasNext: expect.any(Boolean),
               hasPrev: false
             }
           }
         });

         expect(response.body.data.users[0]).toHaveProperty('id');
         expect(response.body.data.users[0]).toHaveProperty('email');
         expect(response.body.data.users[0]).not.toHaveProperty('password');
       });

       test('should filter users by status', async () => {
         const response = await request(app)
           .get('/api/v1/users?status=active')
           .set('Authorization', `Bearer ${authToken}`)
           .expect(200);

         response.body.data.users.forEach(user => {
           expect(user.status).toBe('active');
         });
       });

       test('should return 401 without auth token', async () => {
         const response = await request(app)
           .get('/api/v1/users')
           .expect(401);

         expect(response.body).toMatchObject({
           status: 'error',
           message: 'Access token is required'
         });
       });

       test('should validate pagination parameters', async () => {
         const response = await request(app)
           .get('/api/v1/users?page=0&limit=200')
           .set('Authorization', `Bearer ${authToken}`)
           .expect(400);

         expect(response.body.status).toBe('error');
         expect(response.body.details).toBeDefined();
       });
     });

     describe('POST /api/v1/users', () => {
       test('should create user with valid data', async () => {
         const userData = {
           email: 'newuser@example.com',
           password: 'SecurePass123',
           firstName: 'New',
           lastName: 'User',
           role: 'user'
         };

         const response = await request(app)
           .post('/api/v1/users')
           .set('Authorization', `Bearer ${authToken}`)
           .send(userData)
           .expect(201);

         expect(response.body).toMatchObject({
           status: 'success',
           message: 'User created successfully',
           data: {
             user: {
               email: userData.email,
               firstName: userData.firstName,
               lastName: userData.lastName,
               role: userData.role
             }
           }
         });

         expect(response.body.data.user).not.toHaveProperty('password');
       });

       test('should reject invalid email format', async () => {
         const userData = {
           email: 'invalid-email',
           password: 'SecurePass123',
           firstName: 'Test',
           lastName: 'User'
         };

         const response = await request(app)
           .post('/api/v1/users')
           .set('Authorization', `Bearer ${authToken}`)
           .send(userData)
           .expect(400);

         expect(response.body.status).toBe('error');
         expect(response.body.details.body).toBeDefined();
       });

       test('should reject duplicate email', async () => {
         const userData = {
           email: testUser.email,
           password: 'SecurePass123',
           firstName: 'Test',
           lastName: 'User'
         };

         const response = await request(app)
           .post('/api/v1/users')
           .set('Authorization', `Bearer ${authToken}`)
           .send(userData)
           .expect(409);

         expect(response.body).toMatchObject({
           status: 'error',
           message: 'User with this email already exists'
         });
       });
     });

     describe('Performance Tests', () => {
       test('should handle concurrent requests', async () => {
         const promises = Array(10).fill().map(() =>
           request(app)
             .get('/api/v1/users')
             .set('Authorization', `Bearer ${authToken}`)
         );

         const responses = await Promise.all(promises);
         
         responses.forEach(response => {
           expect(response.status).toBe(200);
         });
       });

       test('should respond within acceptable time', async () => {
         const start = Date.now();
         
         await request(app)
           .get('/api/v1/users')
           .set('Authorization', `Bearer ${authToken}`)
           .expect(200);
         
         const duration = Date.now() - start;
         expect(duration).toBeLessThan(1000); // Should respond within 1 second
       });
     });
   });
   ```

9. **API Versioning Strategy**
   - Implement flexible API versioning:

   **Version Management:**
   ```javascript
   // middleware/versioning.js
   class ApiVersioning {
     static extractVersion(req) {
       // Support multiple versioning strategies
       
       // 1. URL path versioning (preferred)
       const pathVersion = req.path.match(/^\/api\/v(\d+)/);
       if (pathVersion) {
         return parseInt(pathVersion[1]);
       }
       
       // 2. Header versioning
       const headerVersion = req.headers['api-version'];
       if (headerVersion) {
         return parseInt(headerVersion);
       }
       
       // 3. Accept header versioning
       const acceptHeader = req.headers.accept;
       if (acceptHeader) {
         const versionMatch = acceptHeader.match(/application\/vnd\.api\.v(\d+)\+json/);
         if (versionMatch) {
           return parseInt(versionMatch[1]);
         }
       }
       
       // Default to latest version
       return this.getLatestVersion();
     }

     static getLatestVersion() {
       return 1; // Update when new versions are released
     }

     static getSupportedVersions() {
       return [1]; // Add versions as they're created
     }

     static middleware() {
       return (req, res, next) => {
         const requestedVersion = this.extractVersion(req);
         const supportedVersions = this.getSupportedVersions();
         
         if (!supportedVersions.includes(requestedVersion)) {
           return res.status(400).json({
             status: 'error',
             message: `API version ${requestedVersion} is not supported`,
             supportedVersions: supportedVersions,
             latestVersion: this.getLatestVersion()
           });
         }
         
         req.apiVersion = requestedVersion;
         res.set('API-Version', requestedVersion.toString());
         
         next();
       };
     }

     static versionedRoute(versions) {
       return (req, res, next) => {
         const currentVersion = req.apiVersion || this.getLatestVersion();
         
         if (versions[currentVersion]) {
           return versions[currentVersion](req, res, next);
         }
         
         // Fallback to latest version if current version handler not found
         const latestVersion = Math.max(...Object.keys(versions).map(Number));
         if (versions[latestVersion]) {
           return versions[latestVersion](req, res, next);
         }
         
         res.status(501).json({
           status: 'error',
           message: `Version ${currentVersion} is not implemented for this endpoint`
         });
       };
     }
   }

   // Usage example:
   // router.get('/users', ApiVersioning.versionedRoute({
   //   1: userControllerV1.listUsers,
   //   2: userControllerV2.listUsers
   // }));

   module.exports = ApiVersioning;
   ```

10. **Production Monitoring and Analytics**
    - Implement API monitoring and analytics:

    **API Analytics Middleware:**
    ```javascript
    // middleware/analytics.js
    const prometheus = require('prom-client');

    class ApiAnalytics {
      constructor() {
        this.setupMetrics();
      }

      setupMetrics() {
        // Request duration histogram
        this.httpRequestDuration = new prometheus.Histogram({
          name: 'http_request_duration_seconds',
          help: 'Duration of HTTP requests in seconds',
          labelNames: ['method', 'route', 'status_code', 'version'],
          buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10]
        });

        // Request counter
        this.httpRequestsTotal = new prometheus.Counter({
          name: 'http_requests_total',
          help: 'Total number of HTTP requests',
          labelNames: ['method', 'route', 'status_code', 'version']
        });

        // Active connections gauge
        this.activeConnections = new prometheus.Gauge({
          name: 'http_active_connections',
          help: 'Number of active HTTP connections'
        });

        // Error rate counter
        this.httpErrorsTotal = new prometheus.Counter({
          name: 'http_errors_total',
          help: 'Total number of HTTP errors',
          labelNames: ['method', 'route', 'status_code', 'error_type']
        });
      }

      middleware() {
        return (req, res, next) => {
          const startTime = Date.now();
          this.activeConnections.inc();

          res.on('finish', () => {
            const duration = (Date.now() - startTime) / 1000;
            const route = req.route?.path || req.path;
            const version = req.apiVersion || 'unknown';

            const labels = {
              method: req.method,
              route: route,
              status_code: res.statusCode,
              version: version
            };

            // Record metrics
            this.httpRequestDuration.observe(labels, duration);
            this.httpRequestsTotal.inc(labels);
            this.activeConnections.dec();

            // Record errors
            if (res.statusCode >= 400) {
              this.httpErrorsTotal.inc({
                ...labels,
                error_type: this.getErrorType(res.statusCode)
              });
            }

            // Log slow requests
            if (duration > 1) {
              console.warn('Slow request detected:', {
                method: req.method,
                url: req.url,
                duration: duration,
                statusCode: res.statusCode
              });
            }
          });

          next();
        };
      }

      getErrorType(statusCode) {
        if (statusCode >= 400 && statusCode < 500) {
          return 'client_error';
        } else if (statusCode >= 500) {
          return 'server_error';
        }
        return 'unknown';
      }

      getMetrics() {
        return prometheus.register.metrics();
      }
    }

    module.exports = new ApiAnalytics();
    ```