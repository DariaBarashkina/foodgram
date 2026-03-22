# build env
FROM node:21.7.1-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build

FROM alpine:latest
COPY --from=build /app/build /app/build
CMD cp -r /app/build/* /static/