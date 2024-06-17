from flask import Flask, render_template, request, Response, flash, jsonify
import cv2
from keras.models import model_from_json
from keras.preprocessing.image import img_to_array
import numpy as np
import time
import os
import pickle
from sklearn.preprocessing import LabelEncoder
import random  # Import random module here
from flask import redirect


# Turn off oneDNN custom operations
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = Flask(__name__)

# Load model architecture from JSON file
emotion_dict = {0: 'angry', 1: 'happy', 2: 'neutral', 3: 'sad', 4: 'surprise'}
json_file = open('static/emotion_detection/emotion_model1.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
classifier = model_from_json(loaded_model_json)

# Load weights into the model
classifier.load_weights("static/emotion_detection/emotion_model1.h5")

# Load face cascade
try:
    face_cascade = cv2.CascadeClassifier('static/emotion_detection/haarcascade_frontalface_default.xml')
except Exception as e:
    print("Error loading cascade classifiers:", e)

# Load screening model
with open('static/models/screening/model.sav', 'rb') as file:
    loaded_model = pickle.load(file)

@app.route('/')
def index():
    return render_template('index.html')

# Sign up page
@app.route('/signup')
def signup():
    return render_template('signup.html')

# Forgot password page
@app.route('/forgotpassword')
def forgotpassword():
    return render_template('forgotpassword.html')

# Home page
@app.route('/home')
def home():
    return render_template('home.html')

# Chatbot page
# @app.route('/chatbot')
# def chatbot():
#     return render_template('chatbot.html')

# Due to emotion detection
class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.start_time = time.time()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        if elapsed_time >= 5:
            return None

        success, frame = self.video.read()
        if not success:
            return None

        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(img_gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            roi_gray = img_gray[y:y+h, x:x+w]
            roi_gray = cv2.resize(roi_gray, (48, 48), interpolation=cv2.INTER_AREA)

            if np.sum([roi_gray]) != 0:
                roi = roi_gray.astype('float') / 255.0
                roi = img_to_array(roi)
                roi = np.expand_dims(roi, axis=0)
                prediction = classifier.predict(roi)[0]
                maxindex = int(np.argmax(prediction))
                finalout = emotion_dict[maxindex]
                output = str(finalout)

            label_position = (x, y)
            cv2.putText(frame, output, label_position, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame is None:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')







manual_responses = {
            'hello': 'Hello! How can I assist you today?',
            'hi': 'Kindly tell me your name and How May I Assist You further??',
            'appointment': 'To schedule an appointment, please call our office at (123) 456-7890.',
            'prescription': 'You can refill your prescription online through our patient portal.',
            'symptoms': 'If you are experiencing symptoms, please consult a healthcare professional for advice.',
            'covid': 'For information about COVID-19, visit the CDC website or call our COVID-19 hotline at (XXX) XXX-XXXX.',
            'pain': 'If you are experiencing pain, please consult your healthcare provider for proper evaluation and treatment.',
            'medication': 'Please ensure to take your medication as prescribed by your doctor.',
            'emergency': 'In case of emergency, dial 911 immediately for assistance.',
            'insurance': 'For questions regarding insurance coverage, please contact your insurance provider.',
            'diet': 'Maintaining a balanced diet is essential for your overall health and well-being.',
            'exercise': 'Regular exercise can help improve your physical and mental health. Aim for at least 30 minutes of moderate exercise each day.',
            'stress': 'Managing stress is important for your health. Consider practicing relaxation techniques such as deep breathing or meditation.',
            'sleep': 'Getting enough sleep is crucial for your body to function properly. Aim for 7-9 hours of sleep per night.',
            'dehydration': 'Remember to stay hydrated throughout the day by drinking plenty of water.',
            'vaccination': 'Vaccinations are an important part of preventive healthcare. Make sure you are up-to-date on your vaccinations.',
            'blood pressure': 'Monitoring your blood pressure regularly is important for preventing cardiovascular diseases.',
            'cholesterol': 'Maintaining healthy cholesterol levels is important for heart health. Follow a balanced diet and exercise regularly.',
            'diabetes': 'Managing diabetes requires a combination of medication, diet, exercise, and regular monitoring of blood sugar levels.',
            'asthma': 'If you have asthma, make sure to have your inhaler with you at all times and avoid triggers that may exacerbate your symptoms.',
            'allergies': 'Know your allergens and take necessary precautions to avoid exposure to them.',
            'mental health': 'Taking care of your mental health is just as important as taking care of your physical health. Seek help if you are struggling.',
            'nutrition': 'Eating a variety of nutrient-rich foods is essential for optimal health and well-being.',
            'hydration': 'Drink water regularly throughout the day to stay hydrated and support bodily functions.',
            'headache': 'If you have frequent headaches, it\'s important to identify triggers and seek appropriate treatment.',
            'vision': 'Regular eye exams are important for maintaining good vision and detecting any potential eye problems early.',
            'dental': 'Don\'t forget to schedule regular dental check-ups to maintain good oral health.',
            'weight': 'Maintaining a healthy weight is important for reducing the risk of chronic diseases such as heart disease and diabetes.',
            'exercise': 'Incorporating regular physical activity into your routine can help improve your overall health and well-being.',
            'medication': 'Remember to take your medication as prescribed by your doctor and follow any instructions carefully.',
            'emergency': 'In case of a medical emergency, dial 911 immediately for assistance.',
            'insurance': 'If you have questions about your insurance coverage, contact your insurance provider for assistance.',
            'diet': 'Eating a balanced diet that includes plenty of fruits, vegetables, whole grains, and lean proteins is important for good health.',
            'stress': 'Finding healthy ways to cope with stress, such as exercise, meditation, or spending time with loved ones, can help improve your overall well-being.',
            'sleep': 'Getting enough sleep is essential for good health. Aim for 7-9 hours of quality sleep each night.',
            'dehydration': 'Remember to drink plenty of water throughout the day to stay hydrated and maintain proper bodily function.',
            'vaccination': 'Vaccines are an important part of preventive healthcare.Make sure you are up to date on all recommended vaccines.',
            'Blood pressure': 'Monitoring your blood pressure regularly and making lifestyle changes as needed can help prevent hypertension and its complications.',
            'Cholesterol': 'Maintaining healthy cholesterol levels through diet, exercise, and medication if necessary is important for heart health.',
            'Diabetes': 'Managing diabetes through medication, diet, exercise, and regular monitoring of blood sugar levels is essential for preventing complications.',
            'Asthma': 'If you have asthma, make sure to have an action plan in place and carry your inhaler with you at all times.',
            'Allergies': 'Know your allergens and take steps to avoid exposure to them to prevent allergic reactions.',
            'Mental health': 'Taking care of your mental health is just as important as taking care of your physical health. Don\'t hesitate to seek help if you need it.',
            'Nutrition': 'Eating a balanced diet that includes a variety of nutrient-rich foods is key to maintaining good health and preventing chronic diseases.',
            'Hydration': 'Drink plenty of water throughout the day to stay hydrated and support proper bodily function.',
            'Headache': 'If you experience frequent headaches, it\'s important to identify triggers and seek appropriate treatment.',
            'Vision': 'Regular eye exams are important for maintaining good vision and detecting any potential eye problems early.',
            'Dental': 'Don\'t forget to schedule regular dental check-ups to maintain good oral health.',
            'Weight': 'Maintaining a healthy weight is important for reducing the risk of chronic diseases such as heart disease and diabetes.',
            'Exercise': 'Incorporating regular physical activity into your routine can help improve your overall health and well-being.',
            'Medication': 'Remember to take your medication as prescribed by your doctor and follow any instructions carefully.',
            'Emergency': 'In case of a medical emergency, dial 102 immediately for assistance.',
            'Insurance': 'If you have questions about your insurance coverage, contact your insurance provider for assistance.',
            'Diet': 'Eating a balanced diet that includes plenty of fruits, vegetables, whole grains, and lean proteins is important for good health.',
            'Stress': 'Finding healthy ways to cope with stress, such as exercise, meditation, or spending time with loved ones, can help improve your overall well-being.',
            'Sleep': 'Getting enough sleep is essential for good health. Aim for 7-9 hours of quality sleep each night.',
            'Dehydration': 'Remember to drink plenty of water throughout the day to stay hydrated and maintain proper bodily function.',
            'Vaccination': 'Vaccines are an important part of preventive healthcare. Make sure you are up to date on all recommended vaccines.',
            'Blood pressure': 'Monitoring your blood pressure regularly and making lifestyle changes as needed can help prevent hypertension and its complications.',
            'Cholesterol': 'Maintaining healthy cholesterol levels through diet, exercise, and medication if necessary is important for heart health.',
            'Diabetes': 'Managing diabetes through medication, diet, exercise, and regular monitoring of blood sugar levels is essential for preventing complications.',
            'Asthma': 'If you have asthma, make sure to have an action plan in place and carry your inhaler with you at all times.',
            'Allergies': 'Know your allergens and take steps to avoid exposure to them to prevent allergic reactions.',
            'Mental health': 'Taking care of your mental health is just as important as taking care of your physical health. Don\'t hesitate to seek help if you need it.',
            'Nutrition': 'Eating a balanced diet that includes a variety of nutrient-rich foods is key to maintaining good health and preventing chronic diseases.',
            'Hydration': 'Drink plenty of water throughout the day to stay hydrated and support proper bodily function.',
            'Headache': 'If you experience frequent headaches, it\'s important to identify triggers and seek appropriate treatment.',
            'Vision': 'Regular eye exams are important for maintaining good vision and detecting any potential eye problems early.',
            'Dental': 'Don\'t forget to schedule regular dental check-ups to maintain good oral health.',
            'Weight': 'Maintaining a healthy weight is important for reducing the risk of chronic diseases such as heart disease and diabetes.',
            'Exercise': 'Incorporating regular physical activity into your routine can help improve your overall health and well-being.',
            'Medication': 'Remember to take your medication as prescribed by your doctor and follow any instructions carefully.',
            'Insurance': 'If you have questions about your insurance coverage, contact your insurance provider for assistance.',
            'Diet': 'Eating a balanced diet that includes plenty of fruits, vegetables, whole grains, and lean proteins is important for good health.',
            'Stress': 'Finding healthy ways to cope with stress, such as exercise, meditation, or spending time with loved ones, can help improve your overall well-being.',
            'Sleep': 'Getting enough sleep is essential for good health. Aim for 7-9 hours of quality sleep each night.',
            'Dehyddration': 'Remember to drink plenty of water throughout the day to stay hydrated and maintain proper bodily function.',
            'wound care': 'Proper wound care involves cleaning the wound, applying medication or dressing as directed, and monitoring for signs of infection or complications.',
            'burn treatment': 'Treating burns depends on the severity and extent of the injury, but may involve cooling the burn with water, applying aloe vera or antibiotic ointment, and covering with a sterile bandage.',
            'poison control': 'If you suspect poisoning, call Poison Control immediately for guidance on what to do next. Do not induce vomiting unless instructed to do so by a healthcare professional.',
            'emergency contraception': 'Emergency contraception, also known as the morning-after pill, can help prevent pregnancy after unprotected sex or contraceptive failure. It is most effective when taken as soon as possible after intercourse.',
            'contraception options': 'There are many contraceptive options available, including birth control pills, patches, injections, implants, intrauterine devices (IUDs), condoms, and sterilization procedures. Talk to your healthcare provider to find the method that is right for you.',
            'sexually transmitted infections': 'Sexually transmitted infections (STIs) can be prevented by practicing safe sex, including the use of condoms, getting tested regularly, and discussing sexual health openly with partners.',
            'sexual health screenings': 'Regular sexual health screenings are important for detecting STIs early and preventing their spread. These screenings may include tests for HIV, chlamydia, gonorrhea, syphilis, and other infections.',
            'sexual dysfunction': 'Sexual dysfunction can have physical or psychological causes and may require medical evaluation and treatment. Options may include counseling, medication, hormone therapy, or lifestyle changes.',
            'reproductive health': 'Reproductive health encompasses a wide range of topics related to sexual and reproductive wellness, including contraception, fertility, pregnancy, childbirth, and menopause.',
            'fertility awareness': 'Fertility awareness methods involve tracking menstrual cycles and signs of fertility to identify fertile and infertile days for the purpose of achieving or avoiding pregnancy. These methods may include tracking basal body temperature, cervical mucus, and menstrual cycle length.',
            'fertility treatment': 'Fertility treatment options include medications to stimulate ovulation, intrauterine insemination (IUI), in vitro fertilization (IVF), and other assisted reproductive technologies (ART) to help individuals and couples conceive.',
            'pregnancy complications': 'Pregnancy complications can arise at any stage of pregnancy and may include gestational diabetes, preeclampsia, placental abnormalities, preterm labor, and fetal growth restriction. Early prenatal care and monitoring can help detect and manage these issues.',
            'high-risk pregnancy': 'A high-risk pregnancy may involve factors such as advanced maternal age, multiple gestation, preexisting medical conditions, or a history of pregnancy complications. Close monitoring and specialized care may be necessary to ensure the best possible outcome for mother and baby.',
            'prenatal care': 'Regular prenatal care is essential for monitoring the health of both mother and baby during pregnancy. Prenatal visits typically include physical exams, ultrasounds, blood tests, and discussions about nutrition, exercise, and childbirth preparation.',
            'childbirth education': 'Childbirth education classes provide information and support to expectant parents as they prepare for labor, delivery, and the postpartum period. Topics may include breathing techniques, pain management options, childbirth positions, and newborn care.',
            'labor and delivery': 'Labor and delivery involve the process of childbirth, from the onset of contractions to the delivery of the baby and placenta. Labor can be divided into three stages: early labor, active labor, and transition, followed by the pushing stage and delivery of the baby.',
            'pain management in labor': 'Pain management options during labor may include relaxation techniques, breathing exercises, massage, hydrotherapy, medication such as epidurals or opioids, and non-pharmacological methods like acupuncture or hypnosis.',
            'cesarean birth': 'A cesarean birth, or C-section, is a surgical procedure used to deliver a baby through an incision in the abdomen and uterus. It may be planned in advance for medical reasons or performed as an emergency intervention during labor.',
            'postpartum recovery': 'Postpartum recovery involves physical and emotional healing following childbirth. It may include managing pain, fatigue, and hormonal changes, as well as adjusting to breastfeeding, caring for a newborn, and coping with sleep deprivation and mood swings.',
            'breastfeeding support': 'Breastfeeding support services provide education, counseling, and resources to help mothers and babies successfully breastfeed. This may include lactation consultants, breastfeeding classes, support groups, and peer counseling programs.',
            'infant feeding': 'Feeding a newborn involves breastfeeding, formula feeding, or a combination of both, depending on the mother\'s preference and circumstances. It\'s important to feed infants on demand, watch for hunger cues, and ensure proper latch and positioning during breastfeeding.',
            'newborn care': 'Newborn care encompasses a variety of tasks, including feeding, diapering, bathing, soothing, and monitoring for signs of health or developmental concerns. Parents should seek guidance from healthcare providers and trusted resources to ensure their baby\'s well-being.',
            'baby milestones': 'Babies reach developmental milestones at their own pace, but typical milestones during the first year of life include rolling over, sitting up, crawling, babbling, and eventually walking and talking. Regular pediatric check-ups can help monitor development and identify any delays or concerns.',
            'vaccination schedule': 'Following the recommended vaccination schedule helps protect children from serious and potentially life-threatening diseases. Immunizations are typically given at specific ages to provide optimal protection.',
            'childhood illnesses': 'Common childhood illnesses include colds, flu, ear infections, strep throat, chickenpox, and stomach bugs. Most minor illnesses can be managed at home with rest, fluids, and over-the-counter remedies, but serious or persistent symptoms may require medical attention.',
            'pediatric emergencies': 'Pediatric emergencies may include choking, breathing difficulties, severe allergic reactions, high fever, head injuries, seizures, and other sudden or life-threatening conditions. Parents should be prepared to respond quickly and seek emergency medical care as needed.',
            'school health': 'Maintaining good health in school involves eating a nutritious diet, getting regular exercise, practicing good hygiene, managing stress, and seeking help for physical or emotional concerns as needed.',
            'school physicals': 'School physicals ensure that children and adolescents are healthy and ready to participate in academic and extracurricular activities. They may include a physical exam, vision and hearing tests, and screenings for health or developmental issues.',
            'sports physicals': 'Sports physicals assess an individual\'s overall health and fitness level to ensure they can safely participate in athletic activities. They may include a medical history review, physical exam, and assessment of injury risk factors.',
            'school immunizations': 'School immunization requirements vary by state and school district but typically include vaccines to protect against diseases such as measles, mumps, rubella, tetanus, diphtheria, pertussis, polio, hepatitis B, and varicella (chickenpox).',
            'school nurse': 'School nurses play a vital role in promoting student health and wellness by providing basic medical care, administering medications, managing chronic conditions, and responding to medical emergencies during the school day.',
            'school counseling': 'School counselors provide academic, social, emotional, and career support to students, helping them navigate challenges, set goals, make decisions, and develop the skills needed for success in school and beyond.',
            'bullying prevention': 'Bullying prevention efforts aim to create safe and supportive school environments where all students feel respected, valued, and included. This may involve education, awareness campaigns, peer support programs, and clear policies and procedures for addressing bullying behavior.',
            'mental health education': 'Mental health education in schools promotes awareness, understanding, and destigmatization of mental health issues, teaches coping skills and resilience-building strategies, and connects students with appropriate resources and support services.',
            'substance abuse prevention': 'Substance abuse prevention programs in schools aim to educate students about the risks and consequences of drug and alcohol use, teach refusal skills and healthy coping mechanisms, and promote positive peer influences and healthy lifestyles.',
            'nutrition education': 'Nutrition education teaches students about the importance of healthy eating habits, balanced diets, portion control, and making informed food choices to support overall health and well-being. It may include lessons, activities, and hands-on experiences with meal planning, cooking, and gardening.',
            'physical education': 'Physical education (PE) classes promote physical fitness, motor skills development, teamwork, sportsmanship, and lifelong physical activity habits. PE curricula may include a variety of activities such as sports, games, dance, yoga, and fitness challenges.',
            'sleep education': 'Sleep education programs educate students about the importance of good sleep hygiene, the effects of sleep deprivation on health and academic performance, and strategies for improving sleep quality and quantity. This may include tips for establishing bedtime routines, creating sleep-friendly environments, and managing screen time.',
            'sexual health education': 'Sexual health education provides accurate, age-appropriate information about human sexuality, reproductive anatomy and physiology, contraception, STI prevention, consent, healthy relationships, and LGBTQ+ issues. It empowers students to make informed decisions and practice responsible sexual behaviors.',
            'teen pregnancy prevention': 'Teen pregnancy prevention programs aim to reduce rates of unplanned pregnancy among adolescents by providing comprehensive sexuality education, access to contraception and reproductive health services, support for healthy relationships and decision-making skills, and opportunities for youth leadership and advocacy.',
            'school-based health centers': 'School-based health centers offer a range of primary care, mental health, and preventive health services to students on school campuses, providing convenient access to medical care, counseling, health education, and referrals to community resources.',
            'telehealth in schools': 'Telehealth services in schools use technology to connect students with healthcare providers remotely, allowing for virtual medical consultations, counseling sessions, medication management, and follow-up care without the need for in-person visits to a doctor\'s office or clinic.',
            'home schooling health': 'Health and wellness are important considerations for families who choose to homeschool their children, and parents may seek resources and support for promoting physical, emotional, and social well-being outside of a traditional school setting.',
            'special education services': 'Special education services provide individualized support and accommodations for students with disabilities or special needs, ensuring access to a free and appropriate public education (FAPE) and opportunities for academic, social, and emotional growth.',
            'inclusive education': 'Inclusive education practices promote diversity, equity, and belonging in schools by welcoming and supporting students of all abilities, backgrounds, and identities. This may involve adapting curriculum, modifying teaching strategies, fostering peer relationships, and creating inclusive environments where all learners can thrive.',
            'school safety': 'School safety measures aim to protect students, staff, and visitors from physical harm, accidents, violence, and emergencies. This may include security protocols, emergency preparedness plans, safety drills, bullying prevention efforts, mental health supports, and crisis intervention strategies.',
            'health education curriculum': 'Health education curricula provide structured learning experiences that address a wide range of health topics and skills, including nutrition, physical activity, hygiene, safety, sexuality, substance abuse prevention, mental health, and decision-making.',
            'health literacy': 'Health literacy is the ability to find, understand, evaluate, and use health information to make informed decisions and advocate for personal and community health. It involves critical thinking, communication skills, and self-advocacy abilities that empower individuals to navigate the healthcare system and manage their own health effectively.',
            'school wellness policy': 'A school wellness policy is a written document that outlines goals, strategies, and guidelines for promoting health and wellness in schools, including nutrition standards, physical activity initiatives, health education requirements, and wellness promotion activities. It may be developed collaboratively with input from stakeholders such as students, parents, teachers, administrators, and community members.',
            'community partnerships': 'Community partnerships bring together schools, healthcare providers, government agencies, businesses, nonprofits, faith-based organizations, and other stakeholders to collaborate on initiatives that promote health and well-being in the community. These partnerships may involve sharing resources, coordinating services, advocating for policy changes, and addressing social determinants of health.',
            'health equity': 'Health equity means that everyone has the opportunity to attain their highest level of health, regardless of race, ethnicity, socioeconomic status, gender identity, sexual orientation, disability, or other social factors. Achieving health equity requires addressing systemic barriers to health and ensuring that all individuals have access to quality healthcare, education, employment, housing, and other resources that support health and well-being.',
            'school-based nutrition programs': 'School-based nutrition programs provide healthy meals, snacks, and beverages to students during the school day, supporting their nutritional needs, promoting healthy eating habits, and reducing food insecurity. These programs may include school breakfast, lunch, snack, and summer meal programs, as well as nutrition education and outreach efforts.',
            'food allergy management': 'Food allergy management in schools involves identifying students with food allergies, creating individualized allergy action plans, educating staff and students about allergens and emergency procedures, implementing allergen avoidance strategies, and ensuring access to safe meals and snacks.',
            'school gardening programs': 'School gardening programs engage students in hands-on learning experiences that promote environmental stewardship, healthy eating, and outdoor physical activity. Participants learn about gardening, nutrition, science, math, ecology, and sustainability while cultivating fruits, vegetables, herbs, and flowers in school gardens.',
            'mental health resources': 'Mental health resources for students may include school counselors, psychologists, social workers, and other mental health professionals who provide individual and group counseling, crisis intervention, psychoeducation, and referral services. Schools may also offer peer support programs, support groups, wellness activities, and access to community-based mental health providers.',
            'suicide prevention': 'Suicide prevention efforts in schools aim to raise awareness, reduce stigma, identify risk factors and warning signs, promote help-seeking behaviors, and provide support and resources for individuals at risk of suicide. This may include training for school staff, crisis hotlines, mental health screenings, and access to counseling services.',
            'substance use prevention': 'Substance use prevention programs in schools aim to delay the onset of substance use, reduce experimentation, and prevent the development of substance use disorders among students. These programs may focus on alcohol, tobacco, marijuana, prescription drugs, and other substances, and may include education, skill-building, peer support, and policy initiatives.',
            'sexual violence prevention': 'Sexual violence prevention efforts in schools aim to create safe, respectful, and supportive environments where all students feel valued and protected from harassment, abuse, and assault. This may involve education on consent, healthy relationships, bystander intervention, and reporting procedures, as well as policies and practices that promote accountability and address sexual misconduct.',
            'health advocacy': 'Health advocacy involves speaking up and taking action to promote policies, practices, and resources that support health and well-being in schools, communities, and society at large. Advocates may work to address health disparities, improve access to care, protect vulnerable populations, and advance health equity through education, engagement, and advocacy efforts.',
            'school health assessment': 'A school health assessment evaluates the overall health and well-being of students, staff, and the school community, identifying strengths, needs, and priorities for action. This may involve collecting data on health behaviors, risk factors, health outcomes, school policies and practices, and environmental factors that impact health, and using this information to inform decision-making, planning, and resource allocation.',
            'school health promotion': 'School health promotion initiatives aim to create environments that support and reinforce healthy behaviors, attitudes, and norms among students, staff, families, and the wider community. This may involve implementing evidence-based strategies and interventions to promote physical activity, healthy eating, mental health, sexual health, substance abuse prevention, safety, and overall well-being.',
            'school-based physical activity': 'School-based physical activity programs provide opportunities for students to engage in moderate to vigorous physical activity during the school day, supporting their physical health, fitness, and academic performance. These programs may include physical education classes, recess, intramural sports, active transportation initiatives, and before- and after-school activities that promote movement and active play.',
            'school health policies': 'School health policies establish guidelines, standards, and procedures for promoting health and safety in schools, addressing issues such as nutrition, physical activity, mental health, substance abuse prevention, sexual health, bullying, violence, and emergency preparedness. Policies may be developed at the federal, state, district, or school level and should reflect evidence-based practices, legal requirements, community values, and input from stakeholders.',
            'school-based health education': 'School-based health education curricula provide students with knowledge, skills, and attitudes needed to make informed decisions and take positive actions to protect and promote their health. These curricula may cover topics such as nutrition, physical activity, hygiene, safety, sexuality, substance abuse prevention, mental health, violence prevention, and disease prevention, and are typically delivered by trained health educators using age-appropriate, culturally responsive, and developmentally appropriate instructional methods.',
            'healthful school environment': 'A healthful school environment supports and promotes the physical, emotional, and social well-being of students, staff, and visitors, creating conditions that facilitate healthful choices and behaviors. This may include clean and safe facilities, access to clean air and water, nutritious meals and snacks, opportunities for physical activity and recreation, supportive relationships, positive school culture, and policies that prioritize health and wellness.',
            'family engagement in schools': 'Family engagement in schools involves parents, caregivers, and families partnering with educators, administrators, and community members to support student learning, achievement, and well-being. This may include participating in school activities, volunteering, attending parent-teacher conferences, joining parent-teacher organizations, advocating for their children, supporting homework and academic success, and collaborating on school improvement initiatives.',
            'school health leadership': 'School health leadership involves administrators, educators, and other stakeholders guiding and overseeing efforts to promote health and wellness in schools. This may include establishing a vision and goals for school health, creating policies and procedures to support healthful practices, allocating resources, building partnerships, and fostering a culture of health and well-being that prioritizes the needs of students and the school community.',
            'health equity in education': 'Health equity in education involves ensuring that all students have access to the resources, opportunities, and supports they need to succeed in school and in life, regardless of their race, ethnicity, socioeconomic status, gender, sexual orientation, disability, or other factors. This may require addressing systemic barriers, biases, and inequities in the education system, providing targeted interventions and supports for underserved populations, and fostering inclusive, culturally responsive, and equitable learning environments where all students feel valued, respected, and empowered to reach their full potential.',
            'school health partnerships': 'School health partnerships bring together schools, families, healthcare providers, community organizations, businesses, government agencies, and other stakeholders to collaborate on efforts to promote health and well-being in schools and communities. These partnerships may involve sharing resources, coordinating services, advocating for policy changes, and addressing social determinants of health to improve outcomes for students and the broader community.',
            'school health research': 'School health research examines the impact of various factors on student health, well-being, and academic achievement, identifying effective strategies, interventions, and policies to support healthful practices in schools and communities. This may involve studying the relationship between nutrition, physical activity, mental health, academic performance, and other outcomes, as well as evaluating the effectiveness of school-based programs, policies, and practices in promoting health and wellness.',
            'school-based health promotion': 'School-based health promotion initiatives aim to create environments that support and reinforce healthy behaviors, attitudes, and norms among students, staff, families, and the wider community. This may involve implementing evidence-based strategies and interventions to promote physical activity, healthy eating, mental health, sexual health, substance abuse prevention, safety, and overall well-being.',
            'student well-being': 'Student well-being encompasses physical, emotional, social, and academic dimensions of health, emphasizing the importance of supporting students\' holistic development and ensuring their overall health and happiness. Strategies for promoting student well-being may include fostering positive relationships, providing academic and emotional support, creating safe and inclusive environments, and addressing barriers to learning and success.',
            'school-based mental health services': 'School-based mental health services provide assessment, counseling, therapy, and support for students experiencing emotional or behavioral challenges that impact their academic performance, social relationships, or overall well-being. These services may be provided by school counselors, psychologists, social workers, or other mental health professionals, either individually or in group settings, and may include crisis intervention, prevention programs, and referrals to community resources.',
            'social-emotional learning (SEL)': 'Social-emotional learning (SEL) is the process of acquiring and applying the knowledge, skills, and attitudes needed to understand and manage emotions, set and achieve positive goals, demonstrate empathy and kindness, establish and maintain healthy relationships, and make responsible decisions. SEL programs in schools promote students\' social and emotional development, resilience, and well-being, contributing to their overall success in school and in life.',
            'restorative practices in schools': 'Restorative practices in schools are a set of strategies and approaches that focus on repairing harm, restoring relationships, and building community through dialogue, reflection, and accountability. These practices emphasize empathy, communication, and conflict resolution skills, and aim to create a positive school climate where all members of the community feel valued, respected, and supported.',
            'positive behavior interventions and supports (PBIS)': 'Positive behavior interventions and supports (PBIS) is a framework for promoting positive behavior and preventing challenging behavior in schools by establishing clear expectations, teaching and reinforcing desired behaviors, and providing supports and interventions for students who need additional assistance. PBIS emphasizes a proactive, data-driven approach to behavior management, and aims to create a positive school culture where all students can succeed academically and socially.',
            'trauma-informed schools': 'Trauma-informed schools recognize the prevalence and impact of trauma on students\' lives and aim to create safe, supportive, and nurturing environments that promote healing, resilience, and academic success. These schools integrate trauma-informed practices into all aspects of school culture, policies, and practices, including classroom management, discipline, counseling, and family engagement, and prioritize the well-being of students and staff.',
            'youth mental health first aid': 'Youth Mental Health First Aid is an evidence-based training program designed to teach adults how to recognize the signs and symptoms of mental health problems in young people, offer initial support and assistance, and connect them with appropriate resources and services. This training helps adults build their capacity to respond effectively to youth mental health crises and provide support to students who may be struggling with mental health issues.',
            'resilience in schools': 'Resilience in schools refers to the ability of students, staff, and the school community as a whole to adapt, bounce back, and thrive in the face of adversity, trauma, and stress. Schools can promote resilience by fostering supportive relationships, teaching coping skills and problem-solving strategies, providing opportunities for reflection and growth, and creating environments that promote a sense of belonging, competence, and autonomy.',
            'school-based mindfulness programs': 'School-based mindfulness programs teach students and educators mindfulness practices such as meditation, deep breathing, and relaxation techniques to help reduce stress, improve focus and attention, regulate emotions, and promote overall well-being. These programs may be integrated into the curriculum, offered as standalone courses or activities, and adapted to meet the needs of different grade levels and populations, with the goal of fostering a culture of mindfulness and self-awareness in the school community.',
            'school-based yoga programs': 'School-based yoga programs incorporate yoga and mindfulness practices into the school day to promote physical health, mental well-being, and academic success. These programs may include yoga classes, mindfulness exercises, breathing techniques, and relaxation practices tailored to the needs and interests of students and educators, and may be offered as part of physical education, health education, or wellness initiatives.',
            'school-based meditation programs': 'School-based meditation programs introduce students and educators to meditation and mindfulness practices as tools for reducing stress, improving focus and concentration, enhancing self-awareness, and promoting overall well-being. These programs may include guided meditation sessions, mindfulness exercises, and relaxation techniques adapted to the age, developmental level, and cultural background of participants, and may be offered as standalone activities, integrated into the curriculum, or incorporated into existing wellness programs.',
            'school-based counseling services': 'School-based counseling services provide students with access to mental health support, assessment, counseling, therapy, and crisis intervention services within the school setting, reducing barriers to care and promoting early intervention and prevention. These services may be delivered by school counselors, psychologists, social workers, or other mental health professionals, either individually or in group settings, and may address a wide range of emotional, behavioral, and academic concerns.',
            'school-based health clinics': 'School-based health clinics provide students with access to comprehensive primary care, mental health services, reproductive health care, and preventive health services within the school setting, improving access to care and promoting student health and well-being. These clinics may be staffed by nurse practitioners, physician assistants, physicians, mental health professionals, and other healthcare providers, and may offer a range of services including routine physical exams, immunizations, sick visits, counseling, contraception, and health education.',
            'school-based telehealth services': 'School-based telehealth services use telecommunication technology to connect students with healthcare providers remotely, allowing for virtual medical consultations, mental health counseling sessions, medication management, and follow-up care without the need for in-person visits to a doctor\'s office or clinic. These services expand access to care, reduce barriers to treatment, and promote early intervention and prevention of health issues among students, especially those in underserved or remote areas.',
            'school-based health education programs': 'School-based health education programs provide students with structured learning experiences that promote health literacy, teach essential health knowledge and skills, and support positive health behaviors and attitudes. These programs may cover a wide range of health topics including nutrition, physical activity, sexual health, substance abuse prevention, mental health, safety, and disease prevention, and may be delivered through formal instruction, interactive activities, peer-led initiatives, and community partnerships.',
            'school-based health promotion initiatives': 'School-based health promotion initiatives involve coordinated efforts to create environments that support and reinforce healthy behaviors, attitudes, and norms among students, staff, families, and the wider community. These initiatives may include evidence-based strategies and interventions to promote physical activity, healthy eating, mental health, sexual health, substance abuse prevention, safety, and overall well-being, and may be implemented through policies, programs, partnerships, and environmental changes that prioritize health and wellness in the school setting.',
            'school-based health screenings': 'School-based health screenings identify students who may be at risk for health problems or developmental delays and connect them with appropriate resources and services to address their needs. These screenings may include vision and hearing tests, dental exams, scoliosis screenings, mental health assessments, and evaluations for developmental, behavioral, or learning disabilities, and are typically conducted by trained professionals in collaboration with school nurses, counselors, and healthcare providers.',
            'school-based health fairs': 'School-based health fairs are events that provide students, families, and community members with access to information, resources, and services to promote health and wellness. These fairs may include health screenings, educational workshops, fitness activities, healthy cooking demonstrations, nutrition counseling, mental health resources, and referrals to local healthcare providers and community organizations.',
            'school-based wellness programs': 'School-based wellness programs promote health and well-being among students, staff, and families through initiatives that support physical activity, healthy eating, mental health, and overall wellness. These programs may include physical education classes, nutrition education, mental health services, mindfulness activities, peer support programs, staff wellness initiatives, and policies that create a culture of health and wellness in the school community.',
            'school-based health research': 'School-based health research examines the impact of various factors on student health, well-being, and academic achievement, identifying effective strategies, interventions, and policies to support healthful practices in schools and communities. This may involve studying the relationship between nutrition, physical activity, mental health, academic performance, and other outcomes, as well as evaluating the effectiveness of school-based programs, policies, and practices in promoting health and wellness.',
            'school-based health partnerships': 'School-based health partnerships bring together schools, families, healthcare providers, community organizations, businesses, government agencies, and other stakeholders to collaborate on efforts to promote health and well-being in schools and communities. These partnerships may involve sharing resources, coordinating services, advocating for policy changes, and addressing social determinants of health to improve outcomes for students and the broader community.',
            'school-based health policy': 'School-based health policy encompasses laws, regulations, guidelines, and procedures that govern health and wellness in schools, shaping practices and environments that promote student health, safety, and well-being. These policies may address issues such as nutrition standards, physical activity requirements, mental health services, substance abuse prevention, sexual health education, bullying prevention, safety protocols, and emergency preparedness, and may be developed at the federal, state, district, or school level.',
            'school-based health education': 'School-based health education curricula provide students with knowledge, skills, and attitudes needed to make informed decisions and take positive actions to protect and promote their health. These curricula may cover topics such as nutrition, physical activity, hygiene, safety, sexuality, substance abuse prevention, mental health, violence prevention, and disease prevention, and are typically delivered by trained health educators using age-appropriate, culturally responsive, and developmentally appropriate instructional methods.',
            'school-based health interventions': 'School-based health interventions are targeted efforts to promote health and well-being among students, staff, and families through evidence-based strategies and activities. These interventions may focus on specific health issues such as obesity, mental health, substance abuse, sexual health, or violence prevention, and may include educational programs, counseling services, health screenings, policy changes, environmental modifications, and community partnerships designed to improve health outcomes and reduce health disparities.',
            'school-based health promotion': 'School-based health promotion initiatives aim to create environments that support and reinforce healthy behaviors, attitudes, and norms among students, staff, families, and the wider community. This may involve implementing evidence-based strategies and interventions to promote physical activity, healthy eating, mental health, sexual health, substance abuse prevention, safety, and overall well-being.',
            'school-based mental health services': 'School-based mental health services provide students with access to mental health support, assessment, counseling, therapy, and crisis intervention services within the school setting, reducing barriers to care and promoting early intervention and prevention. These services may be delivered by school counselors, psychologists, social workers, or other mental health professionals, either individually or in group settings, and may address a wide range of emotional, behavioral, and academic concerns.',
            'school-based physical activity programs': 'School-based physical activity programs provide opportunities for students to engage in moderate to vigorous physical activity during the school day, supporting their physical health, fitness, and academic performance. These programs may include physical education classes, recess, intramural sports, active transportation initiatives, and before- and after-school activities that promote movement and active play.',
            'school-based telehealth services': 'School-based telehealth services use telecommunication technology to connect students with healthcare providers remotely, allowing for virtual medical consultations, mental health counseling sessions, medication management, and follow-up care without the need for in-person visits to a doctor\'s office or clinic. These services expand access to care, reduce barriers to treatment, and promote early intervention and prevention of health issues among students, especially those in underserved or remote areas.',
            'school-based wellness programs': 'School-based wellness programs promote health and well-being among students, staff, and families through initiatives that support physical activity, healthy eating, mental health, and overall wellness. These programs may include physical education classes, nutrition education, mental health services, mindfulness activities, peer support programs, staff wellness initiatives, and policies that create a culture of health and wellness in the school community.',
            'school-based health research': 'School-based health research examines the impact of various factors on student health, well-being, and academic achievement, identifying effective strategies, interventions, and policies to support healthful practices in schools and communities. This may involve studying the relationship between nutrition, physical activity, mental health, academic performance, and other outcomes, as well as evaluating the effectiveness of school-based programs, policies, and practices in promoting health and wellness.',
            'school-based health partnerships': 'School-based health partnerships bring together schools, families, healthcare providers, community organizations, businesses, government agencies, and other stakeholders to collaborate on efforts to promote health and well-being in schools and communities. These partnerships may involve sharing resources, coordinating services, advocating for policy changes, and addressing social determinants of health to improve outcomes for students and the broader community.',
            'school-based health policy': 'School-based health policy encompasses laws, regulations, guidelines, and procedures that govern health and wellness in schools, shaping practices and environments that promote student health, safety, and well-being. These policies may address issues such as nutrition standards, physical activity requirements, mental health services, substance abuse prevention, sexual health education, bullying prevention, safety protocols, and emergency preparedness, and may be developed at the federal, state, district, or school level.',
            'school-based health education': 'School-based health education curricula provide students with knowledge, skills, and attitudes needed to make informed decisions and take positive actions to protect and promote their health. These curricula may cover topics such as nutrition, physical activity, hygiene, safety, sexuality, substance abuse prevention, mental health, violence prevention, and disease prevention, and are typically delivered by trained health educators using age-appropriate, culturally responsive, and developmentally appropriate instructional methods.',
            'diabetes management': 'Diabetes management involves monitoring blood sugar levels, following a balanced diet, engaging in regular physical activity, taking prescribed medications (such as insulin or oral medications), and managing stress. It also includes regular medical check-ups and adjustments to treatment plans as needed to maintain blood sugar control and prevent complications.',
            'asthma treatment': 'Asthmad treatment typically involves using inhalers or nebulizers to deliver bronchodilators (such as albuterol) to open the airways and relieve symptoms of wheezing, coughing, and shortness of breath. Controller medications (such as inhaled corticosteroids or leukotriene modifiers) may also be prescribed to reduce inflammation and prevent asthma attacks. In severe cases, oral corticosteroids or biologic therapies may be recommended.',
            'hypertension management': 'Hypertension management includes lifestyle modifications such as adopting a heart-healthy diet (low in sodium and rich in fruits, vegetables, and whole grains), engaging in regular physical activity, maintaining a healthy weight, limiting alcohol intake, and quitting smoking. Medications such as diuretics, ACE inhibitors, ARBs, beta-blockers, calcium channel blockers, and others may also be prescribed to lower blood pressure and reduce the risk of complications.',
            'depression treatment': 'Depression treatment may involve psychotherapy (such as cognitive-behavioral therapy or interpersonal therapy) to address negative thought patterns and improve coping skills, medication (such as selective serotonin reuptake inhibitors or serotonin-norepinephrine reuptake inhibitors) to regulate mood and relieve symptoms, and lifestyle changes (such as regular exercise, healthy eating, stress management, and social support) to support overall well-being. In severe cases, electroconvulsive therapy or transcranial magnetic stimulation may be recommended.',
            'anxiety management': 'Anxiety management strategies include cognitive-behavioral therapy techniques such as relaxation exercises, exposure therapy, and cognitive restructuring to challenge irrational fears and reduce anxiety symptoms. Medications such as selective serotonin reuptake inhibitors, serotonin-norepinephrine reuptake inhibitors, benzodiazepines, or beta-blockers may also be prescribed to manage symptoms and improve quality of life. Lifestyle changes such as regular exercise, healthy sleep habits, stress reduction techniques, and social support networks can also help alleviate anxiety.',
            'arthritis treatment': 'Arthritis treatment aims to reduce pain, inflammation, and stiffness, preserve joint function, and improve overall quality of life. This may involve a combination of medications (such as nonsteroidal anti-inflammatory drugs, analgesics, corticosteroids, disease-modifying antirheumatic drugs, or biologic agents), physical therapy, occupational therapy, assistive devices (such as braces or splints), lifestyle modifications (such as weight management or joint protection techniques), and in some cases, surgery (such as joint replacement or joint fusion).',
            'cancer treatment': 'Cancer treatment varies depending on the type and stage of cancer, but may include surgery to remove tumors, chemotherapy to kill cancer cells, radiation therapy to destroy cancer cells or shrink tumors, immunotherapy to stimulate the immune system to fight cancer, targeted therapy to attack specific cancer cells, hormone therapy to block the growth of hormone-sensitive tumors, or stem cell transplantation to replace diseased bone marrow. Treatment plans may also include supportive care to manage symptoms and side effects, such as pain, nausea, fatigue, or depression.',
            'heart disease management': 'Heart disease management involves lifestyle changes such as adopting a heart-healthy diet (low in saturated fat, cholesterol, and sodium), engaging in regular physical activity, maintaining a healthy weight, quitting smoking, and managing stress. Medications such as statins, beta-blockers, ACE inhibitors, ARBs, diuretics, antiplatelet agents, or anticoagulants may also be prescribed to control blood pressure, cholesterol levels, and blood clotting, and reduce the risk of heart attack or stroke. In some cases, procedures such as angioplasty, stent placement, or bypass surgery may be recommended to restore blood flow to the heart.',
            'Alzheimer\'s disease management': 'Alzheimer\'s disease management focuses on preserving cognitive function, managing behavioral symptoms, and providing supportive care to improve quality of life for individuals with the disease and their caregivers. This may involve medications such as cholinesterase inhibitors (such as donepezil, rivastigmine, or galantamine) to improve cognitive symptoms, or memantine to manage symptoms of moderate to severe Alzheimer\'s disease. Nonpharmacological interventions such as cognitive stimulation, physical exercise, social engagement, and caregiver support programs may also be recommended to help manage symptoms and maintain independence for as long as possible.',
            'diarrhea treatment': 'Diarrhea treatment typically involves replacing lost fluids and electrolytes to prevent dehydration and restore electrolyte balance. This may include drinking oral rehydration solutions (such as Pedialyte or Gatorade), clear broths, or diluted fruit juices, and avoiding beverages that can worsen diarrhea (such as caffeine or alcohol). In some cases, over-the-counter medications such as loperamide (Imodium) or bismuth subsalicylate (Pepto-Bismol) may be used to reduce the frequency of bowel movements and relieve symptoms of diarrhea. Antibiotics may be prescribed for certain types of bacterial diarrhea, but are not usually recommended for viral or parasitic diarrhea unless complications arise.',
            'pneumonia treatment': 'Pneumonia treatment depends on the underlying cause of the infection (such as bacteria, viruses, or fungi) and the severity of symptoms. It may involve antibiotics (such as penicillin, amoxicillin, azithromycin, or levofloxacin) for bacterial pneumonia, antiviral medications (such as oseltamivir or zanamivir) for influenza-related pneumonia, or antifungal medications (such as fluconazole or voriconazole) for fungal pneumonia. Supportive care such as rest, hydration, pain relief, and fever reduction may also be recommended to alleviate symptoms and promote recovery. In severe cases or complications such as respiratory failure, hospitalization and intravenous antibiotics or oxygen therapy may be necessary.',
            'influenza treatment': 'Influenza treatment may include antiviral medications such as oseltamivir (Tamiflu), zanamivir (Relenza), peramivir (Rapivab), or baloxavir marboxil (Xofluza) to reduce the severity and duration of symptoms and prevent complications. These medications work best when started within 48 hours of symptom onset, but may still be beneficial if started later in the course of illness. Supportive care such as rest, hydration, pain relief, and fever reduction can also help alleviate symptoms and promote recovery. In some cases, hospitalization may be necessary for severe influenza or complications such as pneumonia, dehydration, or exacerbation of underlying medical conditions.',
            'bronchitis treatment': 'Bronchitis treatment depends on whether the infection is caused by bacteria or viruses, and may involve antibiotics (such as azithromycin, amoxicillin, or doxycycline) for bacterial bronchitis, or supportive care such as rest, hydration, cough suppressants, and over-the-counter pain relievers to relieve symptoms of viral bronchitis. Inhaled bronchodilators or corticosteroids may also be prescribed to open the airways and reduce inflammation, especially in cases of chronic bronchitis or exacerbations of underlying lung conditions such as asthma or COPD.',
            'sinusitis treatment': 'Sinusitis treatment may involve antibiotics (such as amoxicillin, trimethoprim-sulfamethoxazole, or doxycycline) for bacterial sinus infections, or supportive care such as saline nasal irrigation, nasal decongestants, antihistamines, and over-the-counter pain relievers to relieve symptoms of viral or allergic sinusitis. In cases of chronic or recurrent sinusitis, corticosteroid nasal sprays or oral steroids may be prescribed to reduce inflammation and swelling of the nasal passages, and surgery (such as functional endoscopic sinus surgery) may be recommended to improve drainage and ventilation of the sinuses.',
            'gastroenteritis treatment': 'Gastroenteritis treatment focuses on preventing dehydration, relieving symptoms, and promoting recovery. This may involve drinking plenty of fluids such as water, electrolyte solutions (such as Pedialyte or Gatorade), clear broths, or diluted fruit juices to replace lost fluids and electrolytes, and avoiding foods and beverages that can worsen diarrhea or vomiting (such as caffeine, alcohol, dairy products, fatty or spicy foods). In some cases, over-the-counter medications such as loperamide (Imodium) or bismuth subsalicylate (Pepto-Bismol) may be used to reduce the frequency of bowel movements and relieve symptoms of diarrhea or abdominal cramping. Antibiotics are not usually recommended for viral gastroenteritis unless complications such as severe dehydration or bacterial superinfection occur.',
            'urinary tract infection (UTI) treatment': 'Urinary tract infection (UTI) treatment typically involves antibiotics (such as trimethoprim-sulfamethoxazole, nitrofurantoin, ciprofloxacin, or fosfomycin) to kill the bacteria causing the infection and relieve symptoms such as pain, burning with urination, and frequent urination. It is important to complete the full course of antibiotics as prescribed by your healthcare provider, even if symptoms improve before the medication is finished, to prevent recurrence or antibiotic resistance. Drinking plenty of fluids, urinating frequently, and practicing good hygiene (such as wiping from front to back after using the bathroom) can also help prevent UTIs and promote recovery.',
            'acid reflux treatment': 'Acid reflux treatment may involve lifestyle modifications such as avoiding trigger foods and beverages (such as fatty or spicy foods, citrus fruits, tomato-based products, caffeine, alcohol, and carbonated drinks), eating smaller, more frequent meals, maintaining a healthy weight, quitting smoking, and elevating the head of the bed to reduce nighttime reflux. Medications such as antacids, H2 receptor antagonists (such as ranitidine or famotidine), proton pump inhibitors (such as omeprazole or esomeprazole), or prokinetics (such as metoclopramide) may also be prescribed to reduce stomach acid production, relieve symptoms, and promote healing of the esophagus. In severe cases or complications such as esophagitis, Barrett\'s esophagus, or esophageal strictures, surgery (such as fundoplication) may be recommended to reinforce the lower esophageal sphincter and prevent reflux.',
            'migraine treatment': 'Migraine treatment may involve medications such as analgesics (such as acetaminophen, aspirin, or ibuprofen), triptans (such as sumatriptan or rizatriptan) to relieve migraine pain and associated symptoms such as nausea and sensitivity to light and sound, or preventive medications (such as beta-blockers, anticonvulsants, tricyclic antidepressants, or CGRP inhibitors) to reduce the frequency and severity of migraines. Lifestyle modifications such as getting regular sleep, managing stress, staying hydrated, avoiding trigger foods and beverages, and practicing relaxation techniques or biofeedback may also help prevent migraines and improve quality of life. In some cases, intravenous medications or nerve blocks may be used to treat severe migraines or migraines that do not respond to oral medications.',
            'insomnia treatment': 'Insomnia treatment may involve cognitive-behavioral therapy for insomnia (CBT-I) techniques such as stimulus control, sleep restriction, relaxation training, cognitive therapy, or sleep hygiene education to improve sleep habits, regulate sleep-wake cycles, and reduce anxiety about sleep. Medications such as sedative-hypnotics (such as zolpidem, eszopiclone, or temazepam), melatonin receptor agonists (such as ramelteon), or low-dose antidepressants (such as trazodone or amitriptyline) may also be prescribed to help initiate or maintain sleep, but are generally recommended for short-term use due to potential side effects and risk of dependency. Lifestyle modifications such as establishing a regular sleep schedule, creating a relaxing bedtime routine, limiting caffeine and alcohol intake, and avoiding stimulating activities before bedtime can also help improve sleep quality and duration.',
            'obesity management': 'Obesity management involves adopting a comprehensive approach to weight loss and maintenance that includes dietary modifications, increased physical activity, behavior therapy, and, in some cases, medications or bariatric surgery. This may involve working with a multidisciplinary healthcare team that includes physicians, dietitians, exercise physiologists, psychologists, and other specialists to develop a personalized treatment plan based on individual needs, preferences, and goals. Strategies for weight loss may include following a reduced-calorie diet that is high in fruits, vegetables, whole grains, and lean proteins, engaging in regular physical activity (such as aerobic exercise, strength training, or flexibility exercises) for at least 150 minutes per week, keeping track of food intake and physical activity, identifying and addressing triggers for overeating, practicing stress management techniques, and seeking social support from friends, family members, or support groups. In some cases, medications such as orlistat, phentermine-topiramate, naltrexone-bupropion, or liraglutide may be prescribed to help suppress appetite, reduce food cravings, or block fat absorption, but are generally recommended for individuals with a body mass index (BMI) of 30 or higher or a BMI of 27 or higher with obesity-related health problems. Bariatric surgery such as gastric bypass, gastric sleeve, or adjustable gastric banding may be considered for individuals with severe obesity (BMI of 40 or higher) or moderate obesity (BMI of 35 or higher) with significant obesity-related health problems who have not responded to other weight loss interventions, but is typically reserved for those who have made unsuccessful attempts to lose weight through diet and exercise alone.',
    }





@app.route('/video_feed_emotion')
def video_feed_emotion():
    return Response(gen(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')

# Emotion detection page
@app.route('/emotiondetection')
def emotiondetection():
    return render_template('emotiondetection.html')

# Define the route to handle form submission
@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Get the random number passed from the JavaScript function
    random_number = float(request.form['randomNumber'])

    # Determine the route based on the random number
    if random_number <= 0.5:
        return redirect('/emotion_questionnaire_response1')
    else:
        return redirect('/emotion_questionnaire_response2')


    
@app.route('/emotion_questionnaire', methods=['POST','GET'])
def emotion_questionnaire():
    return render_template('emotion_questionnaire.html')


@app.route('/emotion_questionnaire_response1', methods=['POST','GET'])
def emotion_questionnaire_response1():
    return render_template('emotion_questionnaire_response1.html')


@app.route('/emotion_questionnaire_response2', methods=['POST','GET'])
def emotion_questionnaire_response2():
    return render_template('emotion_questionnaire_response2.html')

   


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Handle the form submission (login logic)
        # This block will execute when the form is submitted
        # You can access form data using request.form
        
        # Example:
        username = request.form['username']
        password = request.form['password']
        # Validate credentials, authenticate user, etc.

        # After handling login logic, you can redirect the user to another page
        # For example, redirect to the home page
        return redirect('/home')

    # If the request method is GET, render the signin page
    return render_template('signin.html')


# Chatbot page
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# @app.route('/chat', methods=['POST', 'GET'])
# def chat():
#     user_input = request.json['user_input'].lower()
#     bot_response = ""
#     for key in manual_responses:
#         if key in user_input:
#             bot_response = manual_responses[key]
#             break
#     else:
#         bot_response = "I'm sorry, I didn't understand that."

#     return jsonify({"response": bot_response})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Ensure the request method is POST
        if request.method == 'POST':
            # Check if the request contains JSON data
            if not request.is_json:
                return jsonify({"response": "Request data is not in JSON format."}), 400

            # Extract user input from the JSON data
            user_input = request.json.get('user_input', '').lower()

            # Process user input and generate bot response
            bot_response = ""
            for key in manual_responses:
                if key in user_input:
                    bot_response = manual_responses[key]
                    break
            else:
                bot_response = "I'm sorry, I didn't understand that."

            # Return bot response in JSON format
            return jsonify({"response": bot_response})

        else:
            # Handle cases where the request method is not POST
            return jsonify({"response": "Method Not Allowed", "error": "POST method expected for this endpoint"}), 405

    except Exception as e:
        print("Error processing request:", e)
        return jsonify({"response": "Error processing request.", "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
