# Deploy Report agent solution in EC2

### 1.Create EC2 instance

- Instance type: t3.xlarge
- Storage: 100GB
- Network settings choose "Allow HTTP traffic from the internet"
- IAM Role: AmazonBedrockFullAccess, AmazonOpenSearchServiceFullAccess


### 2.Launch OpenSearch domain
- In the AWS OpenSearch dashboard, Select "Serveless", click "Get start"
- Click "Create collection", input "Collection name", in the "Collection type", select "Vector search", then click "Next"
- After created the collection, copy the endpoint name in the "OpenSearch endpoint", the endpoint name such as: ja29xxxxxxxxxxxxx.us-east-1.aoss.amazonaws.com, No "https://" prefix.


### 3.Connect to EC2, install the following dependencies:

```
sudo yum update
sudo yum install nginx
sudo yum install tmux -y
sudo yum install git
sudo yum install python3-pip


git clone https://github.com/paulhebo/report_agent.git
cd report_agent
pip3 install -r requriment.txt
```

### 4.configure the environment variables
```
vi .env
```
input the region name, such as: us-east-1
input the opensearch host, the value is the opensearch endpoint name, such as:ja29xxxxxxxxxxxxx.us-east-1.aoss.amazonaws.com, No "https://" prefix.
[option]input the opensearch username and password if have

### 5.Create nginx profiles

```
cd /etc/nginx/conf.d
sudo touch streamlit.conf
sudo chmod 777 streamlit.conf
vi streamlit.conf
```

enter the template:

```
upstream ws-backend {
        server xxx.xxx.xxx.xxx:8501;
}

server {
    listen 80;
    server_name xxx.xxx.xxx.xxx;
    client_max_body_size 100m;

    location / {
            
    proxy_pass http://ws-backend;

    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header Host $http_host;
      proxy_redirect off;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
    }
  }
```

Change the xxx.xxx.xxx.xxx to the EC2 private IP.


### 6. start nginx

```
sudo systemctl start nginx.service
```

### 7.Run streamlit ui stript

```
cd /home/ec2-user/report_agent
tmux
streamlit run web_ui.py.py
```

### 8.Open ui page

Enter the url in the webpage：http://EC2 public IP
