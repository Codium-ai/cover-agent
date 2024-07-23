FROM node:18

ENV NODE_OPTIONS=--openssl-legacy-provider

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000
CMD [ "npm", "start" ]