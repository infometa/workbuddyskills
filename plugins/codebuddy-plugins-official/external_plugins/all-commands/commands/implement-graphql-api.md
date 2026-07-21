---
description: Implement GraphQL API endpoints
category: api-development
---

# Implement GraphQL API

Implement GraphQL API endpoints

## Instructions

1. **GraphQL Setup and Configuration**
   - Set up GraphQL server with Apollo Server or similar
   - Configure schema-first or code-first approach
   - Plan GraphQL architecture and data modeling
   - Set up development tools and introspection
   - Configure GraphQL playground and documentation

2. **Schema Definition and Type System**
   - Define comprehensive GraphQL schema:

   **Schema Definition (SDL):**
   ```graphql
   # schema/schema.graphql
   
   # Scalar types
   scalar DateTime
   scalar EmailAddress
   scalar PhoneNumber
   scalar JSON
   scalar Upload

   # User types and enums
   enum UserRole {
     USER
     ADMIN
     MANAGER
   }

   enum UserStatus {
     ACTIVE
     INACTIVE
     SUSPENDED
     PENDING_VERIFICATION
   }

   type User {
     id: ID!
     email: EmailAddress!
     username: String!
     firstName: String!
     lastName: String!
     fullName: String!
     phone: PhoneNumber
     dateOfBirth: DateTime
     avatar: String
     role: UserRole!
     status: UserStatus!
     emailVerified: Boolean!
     phoneVerified: Boolean!
     profile: UserProfile
     orders(
       first: Int = 10
       after: String
       status: OrderStatus
     ): OrderConnection!
     createdAt: DateTime!
     updatedAt: DateTime!
     lastLoginAt: DateTime
   }

   type UserProfile {
     bio: String
     website: String
     location: String
     timezone: String!
     language: String!
     notificationPreferences: JSON!
     privacySettings: JSON!
   }

   # Product types
   enum ProductStatus {
     DRAFT
     ACTIVE
     INACTIVE
     ARCHIVED
   }

   enum ProductVisibility {
     VISIBLE
     HIDDEN
     CATALOG_ONLY
     SEARCH_ONLY
   }

   type Product {
     id: ID!
     name: String!
     slug: String!
     sku: String!
     description: String
     shortDescription: String
     price: Float!
     comparePrice: Float
     costPrice: Float
     weight: Float
     dimensions: ProductDimensions
     category: Category
     brand: Brand
     vendor: Vendor
     status: ProductStatus!
     visibility: ProductVisibility!
     inventoryTracking: Boolean!
     inventoryQuantity: Int
     lowStockThreshold: Int
     allowBackorder: Boolean!
     requiresShipping: Boolean!
     isDigital: Boolean!
     featured: Boolean!
     tags: [String!]!
     attributes: JSON!
     images: [ProductImage!]!
     variants: [ProductVariant!]!
     reviews(
       first: Int = 10
       after: String
       rating: Int
     ): ReviewConnection!
     averageRating: Float
     reviewCount: Int!
     createdAt: DateTime!
     updatedAt: DateTime!
     publishedAt: DateTime
   }

   type ProductDimensions {
     length: Float
     width: Float
     height: Float
     unit: String!
   }

   type ProductImage {
     id: ID!
     url: String!
     altText: String
     sortOrder: Int!
   }

   type ProductVariant {
     id: ID!
     sku: String!
     price: Float!
     comparePrice: Float
     inventoryQuantity: Int
     attributes: JSON!
     image: ProductImage
   }

   # Order types
   enum OrderStatus {
     PENDING
     PROCESSING
     SHIPPED
     DELIVERED
     CANCELLED
     REFUNDED
     ON_HOLD
   }

   type Order {
     id: ID!
     orderNumber: String!
     user: User
     status: OrderStatus!
     currency: String!
     subtotal: Float!
     taxTotal: Float!
     shippingTotal: Float!
     discountTotal: Float!
     total: Float!
     billingAddress: Address!
     shippingAddress: Address!
     shippingMethod: String
     trackingNumber: String
     items: [OrderItem!]!
     notes: String
     createdAt: DateTime!
     updatedAt: DateTime!
     shippedAt: DateTime
     deliveredAt: DateTime
   }

   type OrderItem {
     id: ID!
     product: Product!
     productVariant: ProductVariant
     quantity: Int!
     unitPrice: Float!
     totalPrice: Float!
     productName: String!
     productSku: String!
     productAttributes: JSON
   }

   type Address {
     firstName: String!
     lastName: String!
     company: String
     addressLine1: String!
     addressLine2: String
     city: String!
     state: String
     postalCode: String!
     country: String!
     phone: PhoneNumber
   }

   # Connection types for pagination
   type UserConnection {
     edges: [UserEdge!]!
     pageInfo: PageInfo!
     totalCount: Int!
   }

   type UserEdge {
     node: User!
     cursor: String!
   }

   type ProductConnection {
     edges: [ProductEdge!]!
     pageInfo: PageInfo!
     totalCount: Int!
   }

   type ProductEdge {
     node: Product!
     cursor: String!
   }

   type OrderConnection {
     edges: [OrderEdge!]!
     pageInfo: PageInfo!
     totalCount: Int!
   }

   type OrderEdge {
     node: Order!
     cursor: String!
   }

   type PageInfo {
     hasNextPage: Boolean!
     hasPreviousPage: Boolean!
     startCursor: String
     endCursor: String
   }

   # Input types
   input CreateUserInput {
     email: EmailAddress!
     password: String!
     firstName: String!
     lastName: String!
     phone: PhoneNumber
     dateOfBirth: DateTime
     role: UserRole = USER
   }

   input UpdateUserInput {
     email: EmailAddress
     firstName: String
     lastName: String
     phone: PhoneNumber
     dateOfBirth: DateTime
     status: UserStatus
   }

   input ProductFilters {
     category: ID
     brand: ID
     priceMin: Float
     priceMax: Float
     status: ProductStatus
     featured: Boolean
     inStock: Boolean
     tags: [String!]
     search: String
   }

   input CreateProductInput {
     name: String!
     slug: String!
     sku: String!
     description: String
     price: Float!
     comparePrice: Float
     categoryId: ID
     brandId: ID
     status: ProductStatus = DRAFT
     inventoryQuantity: Int = 0
     attributes: JSON
     tags: [String!]
   }

   # Root types
   type Query {
     # User queries
     me: User
     user(id: ID!): User
     users(
       first: Int = 10
       after: String
       search: String
       role: UserRole
       status: UserStatus
     ): UserConnection!

     # Product queries
     product(id: ID, slug: String): Product
     products(
       first: Int = 10
       after: String
       filters: ProductFilters
       sortBy: ProductSortBy = CREATED_AT
       sortOrder: SortOrder = DESC
     ): ProductConnection!

     # Order queries
     order(id: ID!): Order
     orders(
       first: Int = 10
       after: String
       status: OrderStatus
       userId: ID
     ): OrderConnection!

     # Search
     search(
       query: String!
       first: Int = 10
       after: String
       types: [SearchType!] = [USER, PRODUCT, ORDER]
     ): SearchConnection!
   }

   type Mutation {
     # Auth mutations
     login(email: EmailAddress!, password: String!): AuthPayload!
     logout: Boolean!
     refreshToken: AuthPayload!
     forgotPassword(email: EmailAddress!): Boolean!
     resetPassword(token: String!, password: String!): AuthPayload!

     # User mutations
     createUser(input: CreateUserInput!): User!
     updateUser(id: ID!, input: UpdateUserInput!): User!
     deleteUser(id: ID!): Boolean!
     updateProfile(input: UpdateProfileInput!): UserProfile!

     # Product mutations
     createProduct(input: CreateProductInput!): Product!
     updateProduct(id: ID!, input: UpdateProductInput!): Product!
     deleteProduct(id: ID!): Boolean!
     uploadProductImage(productId: ID!, file: Upload!): ProductImage!

     # Order mutations
     createOrder(input: CreateOrderInput!): Order!
     updateOrderStatus(id: ID!, status: OrderStatus!): Order!
     addOrderItem(orderId: ID!, input: AddOrderItemInput!): OrderItem!
     removeOrderItem(id: ID!): Boolean!
   }

   type Subscription {
     # Real-time updates
     orderUpdated(userId: ID): Order!
     productUpdated(productId: ID): Product!
     userStatusChanged(userId: ID): User!
     
     # Admin subscriptions
     newOrder: Order!
     lowStockAlert: Product!
   }

   enum ProductSortBy {
     CREATED_AT
     NAME
     PRICE
     RATING
     POPULARITY
   }

   enum SortOrder {
     ASC
     DESC
   }

   enum SearchType {
     USER
     PRODUCT
     ORDER
   }

   type AuthPayload {
     token: String!
     refreshToken: String!
     user: User!
     expiresAt: DateTime!
   }
   ```

3. **Resolver Implementation**
   - Implement comprehensive resolvers:

   **Main Resolvers:**
   ```javascript
   // resolvers/index.js
   const { GraphQLDateTime } = require('graphql-iso-date');
   const { GraphQLEmailAddress, GraphQLPhoneNumber } = require('graphql-scalars');
   const GraphQLJSON = require('graphql-type-json');
   const GraphQLUpload = require('graphql-upload/GraphQLUpload.js');

   const userResolvers = require('./userResolvers');
   const productResolvers = require('./productResolvers');
   const orderResolvers = require('./orderResolvers');
   const searchResolvers = require('./searchResolvers');

   const resolvers = {
     // Custom scalars
     DateTime: GraphQLDateTime,
     EmailAddress: GraphQLEmailAddress,
     PhoneNumber: GraphQLPhoneNumber,
     JSON: GraphQLJSON,
     Upload: GraphQLUpload,

     // Root resolvers
     Query: {
       ...userResolvers.Query,
       ...productResolvers.Query,
       ...orderResolvers.Query,
       ...searchResolvers.Query
     },

     Mutation: {
       ...userResolvers.Mutation,
       ...productResolvers.Mutation,
       ...orderResolvers.Mutation
     },

     Subscription: {
       ...userResolvers.Subscription,
       ...productResolvers.Subscription,
       ...orderResolvers.Subscription
     },

     // Type resolvers
     User: userResolvers.User,
     Product: productResolvers.Product,
     Order: orderResolvers.Order
   };

   module.exports = resolvers;
   ```

   **User Resolvers:**
   ```javascript
   // resolvers/userResolvers.js
   const { AuthenticationError, ForbiddenError, UserInputError } = require('apollo-server-express');
   const { withFilter } = require('graphql-subscriptions');
   const userService = require('../services/userService');
   const { requireAuth, requireRole } = require('../utils/authHelpers');
   const { createConnectionFromArray } = require('../utils/connectionHelpers');

   const userResolvers = {
     Query: {
       async me(parent, args, context) {
         requireAuth(context);
         return await userService.findById(context.user.id);
       },

       async user(parent, { id }, context) {
         requireAuth(context);
         
         const user = await userService.findById(id);
         if (!user) {
           throw new UserInputError('User not found');
         }

         // Privacy check - users can only see their own data unless admin
         if (context.user.id !== user.id && !['admin', 'manager'].includes(context.user.role)) {
           throw new ForbiddenError('Insufficient permissions');
         }

         return user;
       },

       async users(parent, { first, after, search, role, status }, context) {
         requireAuth(context);
         requireRole(context, ['admin', 'manager']);

         const result = await userService.findUsers({
           first,
           after,
           search,
           role,
           status
         });

         return createConnectionFromArray(result.users, {
           first,
           after,
           totalCount: result.totalCount
         });
       }
     },

     Mutation: {
       async createUser(parent, { input }, context) {
         requireAuth(context);
         requireRole(context, ['admin']);

         // Check for existing user
         const existingUser = await userService.findByEmail(input.email);
         if (existingUser) {
           throw new UserInputError('User with this email already exists');
         }

         const user = await userService.createUser(input);
         
         // Publish subscription for real-time updates
         context.pubsub.publish('USER_CREATED', { userCreated: user });
         
         return user;
       },

       async updateUser(parent, { id, input }, context) {
         requireAuth(context);
         
         const existingUser = await userService.findById(id);
         if (!existingUser) {
           throw new UserInputError('User not found');
         }

         // Authorization check
         if (context.user.id !== id && !['admin', 'manager'].includes(context.user.role)) {
           throw new ForbiddenError('Insufficient permissions');
         }

         // Role change restriction
         if (input.role && !['admin'].includes(context.user.role)) {
           throw new ForbiddenError('Insufficient permissions to change user role');
         }

         const updatedUser = await userService.updateUser(id, input);
         
         // Publish subscription
         context.pubsub.publish('USER_UPDATED', { userUpdated: updatedUser });
         
         return updatedUser;
       },

       async deleteUser(parent, { id }, context) {
         requireAuth(context);
         requireRole(context, ['admin']);

         // Prevent self-deletion
         if (context.user.id === id) {
           throw new UserInputError('Cannot delete your own account');
         }

         const existingUser = await userService.findById(id);
         if (!existingUser) {
           throw new UserInputError('User not found');
         }

         await userService.deleteUser(id);
         
         // Publish subscription
         context.pubsub.publish('USER_DELETED', { userDeleted: existingUser });
         
         return true;
       }
     },

     Subscription: {
       userStatusChanged: {
         subscribe: withFilter(
           (parent, args, context) => {
             requireAuth(context);
             return context.pubsub.asyncIterator(['USER_UPDATED']);
           },
           (payload, variables) => {
             // Filter by userId if provided
             return !variables.userId || payload.userUpdated.id === variables.userId;
           }
         )
       }
     },

     // Field resolvers
     User: {
       fullName(parent) {
         return `${parent.firstName} ${parent.lastName}`;
       },

       async profile(parent, args, context) {
         return await userService.getUserProfile(parent.id);
       },

       async orders(parent, { first, after, status }, context) {
         requireAuth(context);
         
         // Users can only see their own orders unless admin
         if (context.user.id !== parent.id && !['admin', 'manager'].includes(context.user.role)) {
           throw new ForbiddenError('Insufficient permissions');
         }

         const result = await userService.getUserOrders(parent.id, {
           first,
           after,
           status
         });

         return createConnectionFromArray(result.orders, {
           first,
           after,
           totalCount: result.totalCount
         });
       }
     }
   };

   module.exports = userResolvers;
   ```

4. **DataLoader for N+1 Problem**
   - Implement efficient data loading:

   **DataLoader Implementation:**
   ```javascript
   // dataLoaders/index.js
   const DataLoader = require('dataloader');
   const userService = require('../services/userService');
   const productService = require('../services/productService');
   const orderService = require('../services/orderService');

   class DataLoaders {
     constructor() {
       this.userLoader = new DataLoader(
         async (userIds) => {
           const users = await userService.findByIds(userIds);
           return userIds.map(id => users.find(user => user.id === id) || null);
         },
         {
           cacheKeyFn: (key) => key.toString(),
           maxBatchSize: 100
         }
       );

       this.userProfileLoader = new DataLoader(
         async (userIds) => {
           const profiles = await userService.getProfilesByUserIds(userIds);
           return userIds.map(id => profiles.find(profile => profile.userId === id) || null);
         }
       );

       this.productLoader = new DataLoader(
         async (productIds) => {
           const products = await productService.findByIds(productIds);
           return productIds.map(id => products.find(product => product.id === id) || null);
         }
       );

       this.productCategoryLoader = new DataLoader(
         async (categoryIds) => {
           const categories = await productService.getCategoriesByIds(categoryIds);
           return categoryIds.map(id => categories.find(category => category.id === id) || null);
         }
       );

       this.productImagesLoader = new DataLoader(
         async (productIds) => {
           const imagesMap = await productService.getImagesByProductIds(productIds);
           return productIds.map(id => imagesMap[id] || []);
         }
       );

       this.orderItemsLoader = new DataLoader(
         async (orderIds) => {
           const itemsMap = await orderService.getItemsByOrderIds(orderIds);
           return orderIds.map(id => itemsMap[id] || []);
         }
       );

       this.productReviewsLoader = new DataLoader(
         async (productIds) => {
           const reviewsMap = await productService.getReviewsByProductIds(productIds);
           return productIds.map(id => reviewsMap[id] || []);
         }
       );
     }

     // Clear all caches
     clearAll() {
       this.userLoader.clearAll();
       this.userProfileLoader.clearAll();
       this.productLoader.clearAll();
       this.productCategoryLoader.clearAll();
       this.productImagesLoader.clearAll();
       this.orderItemsLoader.clearAll();
       this.productReviewsLoader.clearAll();
     }

     // Clear specific cache
     clearUser(userId) {
       this.userLoader.clear(userId);
       this.userProfileLoader.clear(userId);
     }

     clearProduct(productId) {
       this.productLoader.clear(productId);
       this.productImagesLoader.clear(productId);
       this.productReviewsLoader.clear(productId);
     }
   }

   module.exports = DataLoaders;
   ```

5. **Authentication and Authorization**
   - Implement GraphQL-specific auth:

   **Auth Helpers:**
   ```javascript
   // utils/authHelpers.js
   const { AuthenticationError, ForbiddenError } = require('apollo-server-express');
   const jwt = require('jsonwebtoken');
   const userService = require('../services/userService');

   class GraphQLAuth {
     static async getUser(req) {
       const authHeader = req.headers.authorization;
       
       if (!authHeader) {
         return null;
       }

       const token = authHeader.replace('Bearer ', '');
       
       try {
         const decoded = jwt.verify(token, process.env.JWT_SECRET);
         const user = await userService.findById(decoded.userId);
         
         if (!user || user.status !== 'active') {
           return null;
         }

         return user;
       } catch (error) {
         return null;
       }
     }

     static requireAuth(context) {
       if (!context.user) {
         throw new AuthenticationError('Authentication required');
       }
       return context.user;
     }

     static requireRole(context, roles) {
       this.requireAuth(context);
       
       if (!roles.includes(context.user.role)) {
         throw new ForbiddenError(`Requires one of the following roles: ${roles.join(', ')}`);
       }
       
       return context.user;
     }

     static requirePermission(context, permissions) {
       this.requireAuth(context);
       
       const userPermissions = context.user.permissions || [];
       const hasPermission = permissions.some(permission => 
         userPermissions.includes(permission)
       );
       
       if (!hasPermission) {
         throw new ForbiddenError(`Requires one of the following permissions: ${permissions.join(', ')}`);
       }
       
       return context.user;
     }

     static canAccessResource(context, resourceUserId, adminRoles = ['admin', 'manager']) {
       this.requireAuth(context);
       
       const isOwner = context.user.id === resourceUserId;
       const isAdmin = adminRoles.includes(context.user.role);
       
       if (!isOwner && !isAdmin) {
         throw new ForbiddenError('Insufficient permissions to access this resource');
       }
       
       return context.user;
     }
   }

   // Export individual functions for convenience
   const { requireAuth, requireRole, requirePermission, canAccessResource } = GraphQLAuth;

   module.exports = {
     GraphQLAuth,
     requireAuth,
     requireRole,
     requirePermission,
     canAccessResource
   };
   ```

6. **Real-time Subscriptions**
   - Implement GraphQL subscriptions:

   **Subscription Setup:**
   ```javascript
   // subscriptions/index.js
   const { PubSub } = require('graphql-subscriptions');
   const { RedisPubSub } = require('graphql-redis-subscriptions');
   const Redis = require('ioredis');

   // Use Redis for production, in-memory for development
   const createPubSub = () => {
     if (process.env.NODE_ENV === 'production') {
       const redisClient = new Redis(process.env.REDIS_URL);
       return new RedisPubSub({
         publisher: redisClient,
         subscriber: redisClient.duplicate()
       });
     } else {
       return new PubSub();
     }
   };

   const pubsub = createPubSub();

   // Subscription events
   const SUBSCRIPTION_EVENTS = {
     USER_CREATED: 'USER_CREATED',
     USER_UPDATED: 'USER_UPDATED',
     USER_DELETED: 'USER_DELETED',
     ORDER_CREATED: 'ORDER_CREATED',
     ORDER_UPDATED: 'ORDER_UPDATED',
     PRODUCT_UPDATED: 'PRODUCT_UPDATED',
     LOW_STOCK_ALERT: 'LOW_STOCK_ALERT'
   };

   // Subscription resolvers
   const subscriptionResolvers = {
     orderUpdated: {
       subscribe: (parent, { userId }, context) => {
         requireAuth(context);
         
         // Users can only subscribe to their own orders unless admin
         if (userId && context.user.id !== userId && !['admin', 'manager'].includes(context.user.role)) {
           throw new ForbiddenError('Insufficient permissions');
         }
         
         return pubsub.asyncIterator([SUBSCRIPTION_EVENTS.ORDER_UPDATED]);
       },
       resolve: (payload, { userId }) => {
         // Filter by userId if provided
         if (userId && payload.orderUpdated.userId !== userId) {
           return null;
         }
         return payload.orderUpdated;
       }
     },

     productUpdated: {
       subscribe: (parent, { productId }, context) => {
         return pubsub.asyncIterator([SUBSCRIPTION_EVENTS.PRODUCT_UPDATED]);
       },
       resolve: (payload, { productId }) => {
         // Filter by productId if provided
         if (productId && payload.productUpdated.id !== productId) {
           return null;
         }
         return payload.productUpdated;
       }
     },

     userStatusChanged: {
       subscribe: (parent, { userId }, context) => {
         requireAuth(context);
         requireRole(context, ['admin', 'manager']);
         
         return pubsub.asyncIterator([SUBSCRIPTION_EVENTS.USER_UPDATED]);
       },
       resolve: (payload, { userId }) => {
         if (userId && payload.userUpdated.id !== userId) {
           return null;
         }
         return payload.userUpdated;
       }
     },

     newOrder: {
       subscribe: (parent, args, context) => {
         requireAuth(context);
         requireRole(context, ['admin', 'manager']);
         
         return pubsub.asyncIterator([SUBSCRIPTION_EVENTS.ORDER_CREATED]);
       }
     },

     lowStockAlert: {
       subscribe: (parent, args, context) => {
         requireAuth(context);
         requireRole(context, ['admin', 'manager']);
         
         return pubsub.asyncIterator([SUBSCRIPTION_EVENTS.LOW_STOCK_ALERT]);
       }
     }
   };

   module.exports = {
     pubsub,
     SUBSCRIPTION_EVENTS,
     subscriptionResolvers
   };
   ```

7. **Error Handling and Validation**
   - Implement comprehensive error handling:

   **Error Handling:**
   ```javascript
   // utils/errorHandling.js
   const { 
     ApolloError, 
     AuthenticationError, 
     ForbiddenError, 
     UserInputError 
   } = require('apollo-server-express');

   class GraphQLErrorHandler {
     static handleError(error, operation) {
       // Log error for debugging
       console.error('GraphQL Error:', {
         message: error.message,
         operation: operation?.operationName,
         variables: operation?.variables,
         stack: error.stack
       });

       // Database errors
       if (error.code === '23505') { // Unique constraint violation
         return new UserInputError('A record with this information already exists');
       }
       
       if (error.code === '23503') { // Foreign key constraint violation
         return new UserInputError('Referenced record does not exist');
       }

       // Validation errors
       if (error.name === 'ValidationError') {
         const messages = Object.values(error.errors).map(err => err.message);
         return new UserInputError('Validation failed', {
           validationErrors: messages
         });
       }

       // Permission errors
       if (error.message.includes('permission') || error.message.includes('access')) {
         return new ForbiddenError(error.message);
       }

       // Authentication errors
       if (error.message.includes('token') || error.message.includes('auth')) {
         return new AuthenticationError(error.message);
       }

       // Network/external service errors
       if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
         return new ApolloError('External service unavailable', 'SERVICE_UNAVAILABLE');
       }

       // Default to internal error
       return new ApolloError(
         'An unexpected error occurred',
         'INTERNAL_ERROR',
         { originalError: error.message }
       );
     }

     static formatError(error) {
       // Don't expose internal errors in production
       if (process.env.NODE_ENV === 'production' && !error.extensions?.code) {
         return new ApolloError('Internal server error', 'INTERNAL_ERROR');
       }

       // Add request ID for tracking
       if (error.extensions?.requestId) {
         error.extensions.requestId = error.extensions.requestId;
       }

       return error;
     }
   }

   // Input validation helper
   class InputValidator {
     static validateEmail(email) {
       const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
       if (!emailRegex.test(email)) {
         throw new UserInputError('Invalid email format');
       }
     }

     static validatePassword(password) {
       if (password.length < 8) {
         throw new UserInputError('Password must be at least 8 characters long');
       }
       
       if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
         throw new UserInputError('Password must contain uppercase, lowercase, and numeric characters');
       }
     }

     static validatePhoneNumber(phone) {
       const phoneRegex = /^\+?[\d\s\-\(\)]{10,20}$/;
       if (!phoneRegex.test(phone)) {
         throw new UserInputError('Invalid phone number format');
       }
     }

     static validateRequired(value, fieldName) {
       if (!value || (typeof value === 'string' && !value.trim())) {
         throw new UserInputError(`${fieldName} is required`);
       }
     }

     static validateStringLength(value, fieldName, min = 0, max = 255) {
       if (typeof value !== 'string') {
         throw new UserInputError(`${fieldName} must be a string`);
       }
       
       if (value.length < min) {
         throw new UserInputError(`${fieldName} must be at least ${min} characters`);
       }
       
       if (value.length > max) {
         throw new UserInputError(`${fieldName} must not exceed ${max} characters`);
       }
     }

     static validateNumericRange(value, fieldName, min, max) {
       if (typeof value !== 'number' || isNaN(value)) {
         throw new UserInputError(`${fieldName} must be a valid number`);
       }
       
       if (min !== undefined && value < min) {
         throw new UserInputError(`${fieldName} must be at least ${min}`);
       }
       
       if (max !== undefined && value > max) {
         throw new UserInputError(`${fieldName} must not exceed ${max}`);
       }
     }
   }

   module.exports = {
     GraphQLErrorHandler,
     InputValidator
   };
   ```

8. **Performance Optimization**
   - Implement GraphQL performance optimizations:

   **Query Complexity and Depth Limiting:**
   ```javascript
   // utils/queryLimiting.js
   const depthLimit = require('graphql-depth-limit');
   const costAnalysis = require('graphql-query-complexity');

   class QueryLimiting {
     static createDepthLimit(maxDepth = 10) {
       return depthLimit(maxDepth, {
         ignoreIntrospection: true
       });
     }

     static createComplexityAnalysis(maxComplexity = 1000) {
       return costAnalysis({
         maximumComplexity: maxComplexity,
         introspection: true,
         scalarCost: 1,
         objectCost: 1,
         listFactor: 10,
         fieldExtensions: {
           complexity: (options) => {
             // Custom complexity calculation
             const { args, childComplexity } = options;
             
             // List fields have higher complexity
             if (args.first) {
               return childComplexity * Math.min(args.first, 100);
             }
             
             return childComplexity;
           }
         },
         createError: (max, actual) => {
           return new Error(`Query complexity ${actual} exceeds maximum allowed complexity ${max}`);
         }
       });
     }

     static createQueryTimeout(timeout = 30000) {
       return {
         willSendResponse(requestContext) {
           if (requestContext.request.query) {
             setTimeout(() => {
               if (!requestContext.response.http.body) {
                 throw new Error('Query timeout exceeded');
               }
             }, timeout);
           }
         }
       };
     }
   }

   // Query caching
   class QueryCache {
     constructor(ttl = 300) { // 5 minutes default
       this.cache = new Map();
       this.ttl = ttl * 1000; // Convert to milliseconds
     }

     get(query, variables) {
       const key = this.generateKey(query, variables);
       const cached = this.cache.get(key);
       
       if (cached && Date.now() - cached.timestamp < this.ttl) {
         return cached.result;
       }
       
       this.cache.delete(key);
       return null;
     }

     set(query, variables, result) {
       const key = this.generateKey(query, variables);
       this.cache.set(key, {
         result,
         timestamp: Date.now()
       });
     }

     generateKey(query, variables) {
       return `${query}:${JSON.stringify(variables || {})}`;
     }

     clear() {
       this.cache.clear();
     }

     // Middleware for Apollo Server
     static createCachePlugin(ttl = 300) {
       const cache = new QueryCache(ttl);
       
       return {
         requestDidStart() {
           return {
             willSendResponse(requestContext) {
               const { request, response } = requestContext;
               
               // Only cache successful queries
               if (response.http.body && !response.errors) {
                 cache.set(request.query, request.variables, response.http.body);
               }
             },
             
             willSendRequest(requestContext) {
               const { request } = requestContext;
               const cached = cache.get(request.query, request.variables);
               
               if (cached) {
                 requestContext.response.http.body = cached;
                 return;
               }
             }
           };
         }
       };
     }
   }

   module.exports = {
     QueryLimiting,
     QueryCache
   };
   ```

9. **GraphQL Testing**
   - Implement comprehensive GraphQL testing:

   **GraphQL Test Suite:**
   ```javascript
   // tests/graphql/users.test.js
   const { createTestClient } = require('apollo-server-testing');
   const { gql } = require('apollo-server-express');
   const { createTestServer } = require('../helpers/testServer');
   const { createTestUser, getAuthToken } = require('../helpers/testHelpers');

   describe('User GraphQL API', () => {
     let server, query, mutate;
     let testUser, authToken;

     beforeAll(async () => {
       server = await createTestServer();
       const testClient = createTestClient(server);
       query = testClient.query;
       mutate = testClient.mutate;

       testUser = await createTestUser({ role: 'admin' });
       authToken = await getAuthToken(testUser);
     });

     describe('Queries', () => {
       const GET_USERS = gql`
         query GetUsers($first: Int, $search: String) {
           users(first: $first, search: $search) {
             edges {
               node {
                 id
                 email
                 firstName
                 lastName
                 role
                 status
                 createdAt
               }
             }
             pageInfo {
               hasNextPage
               hasPreviousPage
               startCursor
               endCursor
             }
             totalCount
           }
         }
       `;

       test('should return paginated users list', async () => {
         const result = await query({
           query: GET_USERS,
           variables: { first: 10 },
           context: { user: testUser }
         });

         expect(result.errors).toBeUndefined();
         expect(result.data.users).toMatchObject({
           edges: expect.any(Array),
           pageInfo: {
             hasNextPage: expect.any(Boolean),
             hasPreviousPage: expect.any(Boolean)
           },
           totalCount: expect.any(Number)
         });

         if (result.data.users.edges.length > 0) {
           expect(result.data.users.edges[0].node).toHaveProperty('id');
           expect(result.data.users.edges[0].node).toHaveProperty('email');
           expect(result.data.users.edges[0].node).not.toHaveProperty('password');
         }
       });

       test('should filter users by search term', async () => {
         const result = await query({
           query: GET_USERS,
           variables: { search: 'test' },
           context: { user: testUser }
         });

         expect(result.errors).toBeUndefined();
         expect(result.data.users.edges).toEqual(
           expect.arrayContaining([
             expect.objectContaining({
               node: expect.objectContaining({
                 email: expect.stringContaining('test')
               })
             })
           ])
         );
       });

       test('should require authentication', async () => {
         const result = await query({
           query: GET_USERS,
           variables: { first: 10 }
         });

         expect(result.errors).toBeDefined();
         expect(result.errors[0].extensions.code).toBe('UNAUTHENTICATED');
       });

       const GET_ME = gql`
         query GetMe {
           me {
             id
             email
             firstName
             lastName
             profile {
               bio
               website
             }
           }
         }
       `;

       test('should return current user profile', async () => {
         const result = await query({
           query: GET_ME,
           context: { user: testUser }
         });

         expect(result.errors).toBeUndefined();
         expect(result.data.me).toMatchObject({
           id: testUser.id.toString(),
           email: testUser.email,
           firstName: testUser.firstName,
           lastName: testUser.lastName
         });
       });
     });

     describe('Mutations', () => {
       const CREATE_USER = gql`
         mutation CreateUser($input: CreateUserInput!) {
           createUser(input: $input) {
             id
             email
             firstName
             lastName
             role
             status
           }
         }
       `;

       test('should create user with valid input', async () => {
         const userInput = {
           email: 'newuser@example.com',
           password: 'SecurePass123',
           firstName: 'New',
           lastName: 'User',
           role: 'USER'
         };

         const result = await mutate({
           mutation: CREATE_USER,
           variables: { input: userInput },
           context: { user: testUser }
         });

         expect(result.errors).toBeUndefined();
         expect(result.data.createUser).toMatchObject({
           email: userInput.email,
           firstName: userInput.firstName,
           lastName: userInput.lastName,
           role: userInput.role,
           status: 'ACTIVE'
         });
         expect(result.data.createUser).toHaveProperty('id');
       });

       test('should validate email format', async () => {
         const userInput = {
           email: 'invalid-email',
           password: 'SecurePass123',
           firstName: 'Test',
           lastName: 'User'
         };

         const result = await mutate({
           mutation: CREATE_USER,
           variables: { input: userInput },
           context: { user: testUser }
         });

         expect(result.errors).toBeDefined();
         expect(result.errors[0].extensions.code).toBe('BAD_USER_INPUT');
       });

       test('should prevent duplicate email', async () => {
         const userInput = {
           email: testUser.email,
           password: 'SecurePass123',
           firstName: 'Test',
           lastName: 'User'
         };

         const result = await mutate({
           mutation: CREATE_USER,
           variables: { input: userInput },
           context: { user: testUser }
         });

         expect(result.errors).toBeDefined();
         expect(result.errors[0].message).toContain('already exists');
       });
     });

     describe('Subscriptions', () => {
       test('should subscribe to user status changes', (done) => {
         const USER_STATUS_CHANGED = gql`
           subscription UserStatusChanged($userId: ID) {
             userStatusChanged(userId: $userId) {
               id
               status
             }
           }
         `;

         const observable = server.subscription({
           query: USER_STATUS_CHANGED,
           variables: { userId: testUser.id },
           context: { user: testUser }
         });

         observable.subscribe({
           next: (result) => {
             expect(result.data.userStatusChanged).toMatchObject({
               id: testUser.id.toString(),
               status: expect.any(String)
             });
             done();
           },
           error: done
         });

         // Trigger the subscription by updating user status
         setTimeout(() => {
           server.pubsub.publish('USER_UPDATED', {
             userUpdated: { ...testUser, status: 'INACTIVE' }
           });
         }, 100);
       });
     });

     describe('Performance', () => {
       test('should handle complex queries efficiently', async () => {
         const COMPLEX_QUERY = gql`
           query ComplexQuery {
             users(first: 5) {
               edges {
                 node {
                   id
                   email
                   profile {
                     bio
                   }
                   orders(first: 3) {
                     edges {
                       node {
                         id
                         total
                         items {
                           id
                           product {
                             id
                             name
                           }
                         }
                       }
                     }
                   }
                 }
               }
             }
           }
         `;

         const start = Date.now();
         const result = await query({
           query: COMPLEX_QUERY,
           context: { user: testUser }
         });
         const duration = Date.now() - start;

         expect(result.errors).toBeUndefined();
         expect(duration).toBeLessThan(2000); // Should complete within 2 seconds
       });

       test('should limit query depth', async () => {
         const DEEP_QUERY = gql`
           query DeepQuery {
             users {
               edges {
                 node {
                   orders {
                     edges {
                       node {
                         items {
                           product {
                             category {
                               parent {
                                 parent {
                                   parent {
                                     name
                                   }
                                 }
                               }
                             }
                           }
                         }
                       }
                     }
                   }
                 }
               }
             }
           }
         `;

         const result = await query({
           query: DEEP_QUERY,
           context: { user: testUser }
         });

         expect(result.errors).toBeDefined();
         expect(result.errors[0].message).toContain('depth');
       });
     });
   });
   ```

10. **Production Setup and Deployment**
    - Configure GraphQL for production:

    **Production Configuration:**
    ```javascript
    // server/apollo.js
    const { ApolloServer } = require('apollo-server-express');
    const { makeExecutableSchema } = require('@graphql-tools/schema');
    const { shield, rule, and, or } = require('graphql-shield');
    const depthLimit = require('graphql-depth-limit');
    const costAnalysis = require('graphql-query-complexity');

    const typeDefs = require('../schema');
    const resolvers = require('../resolvers');
    const { GraphQLAuth } = require('../utils/authHelpers');
    const { GraphQLErrorHandler } = require('../utils/errorHandling');
    const { QueryLimiting, QueryCache } = require('../utils/queryLimiting');
    const DataLoaders = require('../dataLoaders');
    const { pubsub } = require('../subscriptions');

    // Security rules
    const rules = {
      isAuthenticated: rule({ cache: 'contextual' })(
        async (parent, args, context) => {
          return !!context.user;
        }
      ),
      isAdmin: rule({ cache: 'contextual' })(
        async (parent, args, context) => {
          return context.user && ['admin'].includes(context.user.role);
        }
      ),
      isManagerOrAdmin: rule({ cache: 'contextual' })(
        async (parent, args, context) => {
          return context.user && ['admin', 'manager'].includes(context.user.role);
        }
      )
    };

    const permissions = shield({
      Query: {
        me: rules.isAuthenticated,
        user: rules.isAuthenticated,
        users: rules.isManagerOrAdmin,
        orders: rules.isManagerOrAdmin
      },
      Mutation: {
        createUser: rules.isAdmin,
        updateUser: rules.isAuthenticated,
        deleteUser: rules.isAdmin,
        createProduct: rules.isManagerOrAdmin,
        updateProduct: rules.isManagerOrAdmin,
        deleteProduct: rules.isAdmin
      },
      Subscription: {
        userStatusChanged: rules.isManagerOrAdmin,
        newOrder: rules.isManagerOrAdmin,
        lowStockAlert: rules.isManagerOrAdmin
      }
    }, {
      allowExternalErrors: true,
      fallbackError: 'Not authorized for this operation'
    });

    const createApolloServer = () => {
      const schema = makeExecutableSchema({
        typeDefs,
        resolvers
      });

      return new ApolloServer({
        schema: permissions(schema),
        context: async ({ req, connection }) => {
          // WebSocket connection (subscriptions)
          if (connection) {
            return {
              user: connection.context.user,
              dataLoaders: new DataLoaders(),
              pubsub
            };
          }

          // HTTP request
          const user = await GraphQLAuth.getUser(req);
          
          return {
            user,
            dataLoaders: new DataLoaders(),
            pubsub,
            req
          };
        },
        formatError: GraphQLErrorHandler.formatError,
        validationRules: [
          QueryLimiting.createDepthLimit(10),
          QueryLimiting.createComplexityAnalysis(1000)
        ],
        plugins: [
          QueryCache.createCachePlugin(300), // 5 minutes cache
          {
            requestDidStart() {
              return {
                willSendResponse(requestContext) {
                  // Clear DataLoaders after each request
                  if (requestContext.context.dataLoaders) {
                    requestContext.context.dataLoaders.clearAll();
                  }
                }
              };
            }
          }
        ],
        introspection: process.env.NODE_ENV !== 'production',
        playground: process.env.NODE_ENV !== 'production',
        subscriptions: {
          onConnect: async (connectionParams, webSocket, context) => {
            // Authenticate WebSocket connections
            if (connectionParams.authorization) {
              const user = await GraphQLAuth.getUser({
                headers: { authorization: connectionParams.authorization }
              });
              return { user };
            }
            throw new Error('Missing auth token!');
          },
          onDisconnect: (webSocket, context) => {
            console.log('Client disconnected');
          }
        }
      });
    };

    module.exports = createApolloServer;
    ```